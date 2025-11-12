"""
Sessions API endpoints.

Provides:
- Start Socratic conversation session
- Get next question
- Submit answer and extract specifications
- Get session history
- End session
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..agents.orchestrator import get_orchestrator
from ..core.action_logger import log_session
from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
# Nested router for sessions under projects
project_sessions_router = APIRouter(prefix="/api/v1/projects/{project_id}/sessions", tags=["project-sessions"])


class StartSessionRequest(BaseModel):
    """Request model for starting a session."""
    project_id: str


class SubmitAnswerRequest(BaseModel):
    """Request model for submitting an answer."""
    question_id: str
    answer: str


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message in direct chat mode."""
    message: str


class SetModeRequest(BaseModel):
    """Request model for setting session mode."""
    mode: str  # 'socratic' or 'direct_chat'


class SessionResponse(BaseModel):
    """Response model for session data."""
    id: str
    project_id: str
    status: str
    created_at: str


class SessionListResponse(BaseModel):
    """Response for session list."""
    sessions: list[SessionResponse]
    total: int


@router.get("")
def list_sessions(
    current_user: User = Depends(get_current_active_user)
) -> SessionListResponse:
    """
    List all sessions for the current user.

    Args:
        current_user: Authenticated user

    Returns:
        SessionListResponse with sessions list
    """
    # This endpoint requires authentication
    # For now, return empty list
    return SessionListResponse(
        sessions=[],
        total=0
    )


@router.post("")
def start_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Start a new Socratic conversation session for a project.

    Args:
        request: Session details (project_id)
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'session_id': str,
            'project_id': str,
            'status': str
        }

    Example:
        POST /api/v1/sessions
        Authorization: Bearer <token>
        {
            "project_id": "abc-123"
        }

        Response:
        {
            "success": true,
            "session_id": "session-456",
            "project_id": "abc-123",
            "status": "active"
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {request.project_id}")

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Create session
    # Note: user access is enforced via project ownership check above
    # Session doesn't have user_id field - it's tracked via project.user_id
    session = SessionModel(
        project_id=request.project_id,
        status='active',
        started_at=datetime.now(timezone.utc)
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    # Log session start
    log_session(
        "Session started",
        session_id=str(session.id),
        mode="socratic",
        success=True,
        project_name=project.name if hasattr(project, 'name') else None
    )

    return {
        'success': True,
        'session_id': str(session.id),
        'project_id': str(session.project_id),
        'status': session.status,
        'session': {
            'id': str(session.id),
            'project_id': str(session.project_id),
            'mode': session.mode,
            'status': session.status,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'updated_at': session.updated_at.isoformat() if session.updated_at else None
        }
    }


@router.post("/{session_id}/next-question")
def get_next_question(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get the next Socratic question for the session.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'question_id': str,
            'question': dict with text, category, etc.
        }

    Example:
        POST /api/v1/sessions/session-456/next-question
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "question_id": "q-789",
            "question": {
                "id": "q-789",
                "text": "What is the primary goal of your project?",
                "category": "goals",
                "difficulty": "basic"
            }
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Verify session exists and user has access
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Check session is active
    if session.status != 'active':
        raise HTTPException(status_code=400, detail=f"Session is not active (status: {session.status})")

    # Generate next question using SocraticCounselorAgent
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='socratic',
        action='generate_question',
        data={
            'project_id': str(session.project_id),
            'session_id': session_id
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to generate question')
        )

    return result


@router.post("/{session_id}/answer")
def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Submit answer to a question and extract specifications.

    Args:
        session_id: Session UUID
        request: Answer details (question_id, answer)
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'specs_extracted': int,
            'specifications': List[dict],
            'maturity_score': float
        }

    Example:
        POST /api/v1/sessions/session-456/answer
        Authorization: Bearer <token>
        {
            "question_id": "q-789",
            "answer": "I want to build a FastAPI web application for managing tasks..."
        }

        Response:
        {
            "success": true,
            "specs_extracted": 5,
            "specifications": [
                {
                    "category": "tech_stack",
                    "key": "framework",
                    "value": "FastAPI"
                },
                ...
            ],
            "maturity_score": 12.5
        }
    """
    from ..models.conversation_history import ConversationHistory
    from ..models.project import Project
    from ..models.question import Question
    from ..models.session import Session as SessionModel

    # Verify session exists and user has access
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Check session is active
    if session.status != 'active':
        raise HTTPException(status_code=400, detail=f"Session is not active (status: {session.status})")

    # Verify question exists
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question not found: {request.question_id}")

    # Save to conversation history
    conversation = ConversationHistory(
        session_id=session_id,
        role='user',
        content=request.answer,
        message_metadata={'question_id': str(request.question_id)}
    )
    db.add(conversation)
    db.commit()

    # Extract specifications using ContextAnalyzerAgent
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='context',
        action='extract_specifications',
        data={
            'session_id': session_id,
            'question_id': request.question_id,
            'answer': request.answer,
            'user_id': current_user.id
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to extract specifications')
        )

    # Track question effectiveness for user learning
    try:
        specs_extracted = result.get('specs_extracted', 0)
        answer_length = len(request.answer)

        # Calculate answer quality (0-1): based on specs extracted and answer length
        # Quality = 1.0 if specs_extracted > 0, scaled by answer detail
        answer_quality = min(1.0, (specs_extracted / 5) + (min(answer_length, 500) / 500) * 0.5) if specs_extracted > 0 else 0.3

        learning_result = orchestrator.route_request(
            'learning',
            'track_question_effectiveness',
            {
                'user_id': str(current_user.id),
                'question_template_id': str(request.question_id),
                'role': 'user',  # Default role, can be enhanced later
                'answer_length': answer_length,
                'specs_extracted': specs_extracted,
                'answer_quality': answer_quality
            }
        )

        if learning_result.get('success'):
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Tracked question effectiveness for question {request.question_id}: score={learning_result.get('effectiveness_score', 0):.2f}")
    except Exception as e:
        # Log but don't fail the request if learning tracking fails
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to track question effectiveness: {e}")

    return result


@router.post("/{session_id}/chat")
def send_chat_message(
    session_id: str,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Send a message in direct chat mode.

    Switches session to direct_chat mode if needed and processes the message.

    Args:
        session_id: Session UUID
        request: Chat message details (message)
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'response': str,
            'specs_extracted': int,
            'maturity_score': float
        }

    Example:
        POST /api/v1/sessions/session-456/chat
        Authorization: Bearer <token>
        {
            "message": "I need a user authentication system with email and password"
        }

        Response:
        {
            "success": true,
            "response": "That sounds like a good requirement! Let me clarify...",
            "specs_extracted": 2,
            "maturity_score": 50
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Verify session exists and user has access
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # If session is in socratic mode, switch to direct_chat
    if session.mode != 'direct_chat':
        orchestrator = get_orchestrator()
        toggle_result = orchestrator.route_request(
            'direct_chat',
            'toggle_mode',
            {
                'session_id': session_id,
                'mode': 'direct_chat'
            }
        )
        if not toggle_result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=f"Failed to switch to direct chat mode: {toggle_result.get('error')}"
            )

    # Process chat message through DirectChatAgent
    orchestrator = get_orchestrator()
    result = orchestrator.route_request(
        'direct_chat',
        'process_chat_message',
        {
            'session_id': session_id,
            'user_id': str(current_user.id),
            'message': request.message,
            'project_id': str(session.project_id)
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to process chat message')
        )

    return {
        'success': True,
        'response': result.get('response', ''),
        'specs_extracted': result.get('specs_extracted', 0),
        'maturity_score': result.get('maturity_score', 0)
    }


@router.get("/{session_id}")
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get session details.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'session': dict
        }

    Example:
        GET /api/v1/sessions/session-456
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "session": {
                "id": "session-456",
                "project_id": "abc-123",
                "status": "active",
                "created_at": "2025-01-01T00:00:00Z",
                ...
            }
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        'success': True,
        'session': session.to_dict()  # TODO Parameter 'self' unfilled
    }


@router.get("/{session_id}/history")
def get_session_history(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get conversation history for a session (paginated).

    Args:
        session_id: Session UUID
        skip: Number of messages to skip (default: 0)
        limit: Maximum messages to return (default: 100)
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'history': List[dict],
            'total': int,
            'skip': int,
            'limit': int
        }

    Example:
        GET /api/v1/sessions/session-456/history
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "history": [
                {
                    "speaker": "assistant",
                    "message": "What is the primary goal of your project?",
                    "timestamp": "2025-01-01T00:00:00Z"
                },
                {
                    "speaker": "user",
                    "message": "I want to build a task management app",
                    "timestamp": "2025-01-01T00:01:00Z"
                },
                ...
            ]
        }
    """
    from ..models.conversation_history import ConversationHistory
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Verify session exists and user has access
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get conversation history with pagination
    query = db.query(ConversationHistory).filter(
        ConversationHistory.session_id == session_id
    ).order_by(ConversationHistory.timestamp.asc())

    total = query.count()
    history = query.offset(skip).limit(limit).all()

    return {
        'success': True,
        'history': [h.to_dict() for h in history],  # TODO Parameter 'self' unfilled
        'total': total,
        'skip': skip,
        'limit': limit
    }


@router.post("/{session_id}/end")
def end_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    End a session.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'session_id': str,
            'status': str
        }

    Example:
        POST /api/v1/sessions/session-456/end
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "session_id": "session-456",
            "status": "completed"
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Update session status
    session.status = 'completed'
    db.commit()

    return {
        'success': True,
        'session_id': str(session.id),
        'status': session.status
    }


@router.get("/{session_id}/mode")
def get_session_mode(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get the current mode of a session.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'session_id': str,
            'mode': str,
            'status': str
        }

    Example:
        GET /api/v1/sessions/session-456/mode
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "session_id": "session-456",
            "mode": "socratic",
            "status": "active"
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        'success': True,
        'session_id': str(session.id),
        'mode': session.mode,
        'status': session.status
    }


@router.post("/{session_id}/mode")
def set_session_mode(
    session_id: str,
    request: SetModeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Toggle or set the session mode (socratic or direct_chat).

    Args:
        session_id: Session UUID
        request: Mode setting (mode: 'socratic' or 'direct_chat')
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'session_id': str,
            'old_mode': str,
            'new_mode': str,
            'status': str
        }

    Example:
        POST /api/v1/sessions/session-456/mode
        Authorization: Bearer <token>
        {
            "mode": "direct_chat"
        }

        Response:
        {
            "success": true,
            "session_id": "session-456",
            "old_mode": "socratic",
            "new_mode": "direct_chat",
            "status": "active"
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Validate mode
    if request.mode not in ['socratic', 'direct_chat']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Must be 'socratic' or 'direct_chat'"
        )

    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Check session is active
    if session.status != 'active':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change mode on inactive session (status: {session.status})"
        )

    old_mode = session.mode
    session.mode = request.mode
    db.commit()

    return {
        'success': True,
        'session_id': str(session.id),
        'old_mode': old_mode,
        'new_mode': session.mode,
        'status': session.status
    }


@router.post("/{session_id}/pause")
def pause_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Pause an active session.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'session_id': str,
            'status': str
        }

    Example:
        POST /api/v1/sessions/session-456/pause
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "session_id": "session-456",
            "status": "paused"
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Check session is active
    if session.status != 'active':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause inactive session (status: {session.status})"
        )

    session.status = 'paused'
    db.commit()

    return {
        'success': True,
        'session_id': str(session.id),
        'status': session.status
    }


@router.post("/{session_id}/resume")
def resume_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Resume a paused session.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'session_id': str,
            'status': str
        }

    Example:
        POST /api/v1/sessions/session-456/resume
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "session_id": "session-456",
            "status": "active"
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Check session is paused
    if session.status != 'paused':
        raise HTTPException(
            status_code=400,
            detail=f"Can only resume paused sessions (current status: {session.status})"
        )

    session.status = 'active'
    db.commit()

    return {
        'success': True,
        'session_id': str(session.id),
        'status': session.status
    }


@router.get("")
def list_user_sessions(
    project_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    List sessions for the current user, optionally filtered by project.

    Args:
        project_id: Optional project ID to filter sessions
        skip: Number of sessions to skip (default: 0)
        limit: Maximum sessions to return (default: 100)
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'sessions': [
                {
                    'id': str,
                    'project_id': str,
                    'mode': str,
                    'status': str,
                    'started_at': str (ISO format),
                    'ended_at': str or null,
                    'created_at': str (ISO format),
                    'updated_at': str (ISO format)
                }
            ],
            'total': int
        }
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Build query for sessions belonging to user's projects
    query = db.query(SessionModel).join(
        Project, SessionModel.project_id == Project.id
    ).filter(Project.user_id == current_user.id)

    # Filter by project_id if provided
    if project_id:
        query = query.filter(SessionModel.project_id == project_id)

    total = query.count()
    sessions = query.offset(skip).limit(limit).all()

    return {
        'success': True,
        'sessions': [
            {
                'id': str(session.id),
                'project_id': str(session.project_id),
                'mode': session.mode,
                'status': session.status,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'ended_at': session.ended_at.isoformat() if session.ended_at else None,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'updated_at': session.updated_at.isoformat() if session.updated_at else None
            }
            for session in sessions
        ],
        'total': total
    }


# ============================================================================
# Nested Endpoints: Sessions under Projects
# ============================================================================


class CreateProjectSessionRequest(BaseModel):
    """Request model for creating a session under a project."""
    name: str
    description: str
    status: str = "active"


class UpdateProjectSessionRequest(BaseModel):
    """Request model for updating a session under a project."""
    status: str = None
    name: str = None
    description: str = None


@project_sessions_router.get("")
def list_project_sessions(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> list:
    """
    List all sessions for a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        List of session objects
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    # Get sessions for this project
    sessions = db.query(SessionModel).filter(
        SessionModel.project_id == project_id
    ).all()

    return [
        {
            "id": str(s.id),
            "project_id": str(s.project_id),
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in sessions
    ]


@project_sessions_router.post("", status_code=status.HTTP_201_CREATED)
def create_project_session(
    project_id: str,
    request: CreateProjectSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Create a new session for a project.

    Args:
        project_id: Project UUID
        request: Session details
        current_user: Authenticated user
        db: Database session

    Returns:
        Created session details
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    # Create session
    session = SessionModel(
        project_id=project_id,
        name=request.name,
        description=request.description,
        status=request.status,
        started_at=datetime.now(timezone.utc)
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "id": str(session.id),
        "project_id": str(session.project_id),
        "name": request.name,
        "description": request.description,
        "status": request.status,
        "created_at": session.created_at.isoformat() if session.created_at else None
    }


@project_sessions_router.get("/{session_id}")
def get_project_session(
    project_id: str,
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get details of a session in a project.

    Args:
        project_id: Project UUID
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Session details
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    # Get session
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.project_id == project_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    return {
        "id": str(session.id),
        "project_id": str(session.project_id),
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else None
    }


@project_sessions_router.patch("/{session_id}")
def update_project_session(
    project_id: str,
    session_id: str,
    request: UpdateProjectSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Update a session in a project.

    Args:
        project_id: Project UUID
        session_id: Session UUID
        request: Fields to update
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated session details
    """
    from ..models.project import Project
    from ..models.session import Session as SessionModel

    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    # Get session
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.project_id == project_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    # Update fields if provided
    if request.status is not None:
        session.status = request.status
    if request.name is not None:
        session.name = request.name
    if request.description is not None:
        session.description = request.description

    db.commit()
    db.refresh(session)

    return {
        "id": str(session.id),
        "project_id": str(session.project_id),
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else None
    }
