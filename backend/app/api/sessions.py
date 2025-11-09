"""
Sessions API endpoints.

Provides:
- Start Socratic conversation session
- Get next question
- Submit answer and extract specifications
- Get session history
- End session
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..agents.orchestrator import get_orchestrator

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


class StartSessionRequest(BaseModel):
    """Request model for starting a session."""
    project_id: str


class SubmitAnswerRequest(BaseModel):
    """Request model for submitting an answer."""
    question_id: str
    answer: str


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

    return {
        'success': True,
        'session_id': str(session.id),
        'project_id': str(session.project_id),
        'status': session.status
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
    from ..models.session import Session as SessionModel
    from ..models.project import Project

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
    from ..models.session import Session as SessionModel
    from ..models.conversation_history import ConversationHistory
    from ..models.question import Question
    from ..models.project import Project

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

    return result


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
    from ..models.session import Session as SessionModel
    from ..models.project import Project

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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get conversation history for a session.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'history': List[dict]
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
    from ..models.session import Session as SessionModel
    from ..models.conversation_history import ConversationHistory
    from ..models.project import Project

    # Verify session exists and user has access
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Check project ownership
    project = db.query(Project).filter(Project.id == session.project_id).first()
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get conversation history
    history = db.query(ConversationHistory).filter(
        ConversationHistory.session_id == session_id
    ).order_by(ConversationHistory.timestamp.asc()).all()

    return {
        'success': True,
        'history': [h.to_dict() for h in history]  # TODO Parameter 'self' unfilled
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
    from ..models.session import Session as SessionModel
    from ..models.project import Project

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
