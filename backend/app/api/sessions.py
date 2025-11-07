"""
Sessions API Endpoints

Provides session management including mode toggling and direct chat.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, UUID4
from typing import Optional

from ..core.dependencies import get_current_user, get_orchestrator
from ..agents.orchestrator import AgentOrchestrator
from ..models import User

router = APIRouter(prefix="/sessions", tags=["sessions"])


class ToggleModeRequest(BaseModel):
    """Request model for toggling session mode"""
    mode: str  # 'socratic' or 'direct_chat'


class ChatMessageRequest(BaseModel):
    """Request model for sending chat message"""
    message: str


class ToggleModeResponse(BaseModel):
    """Response model for toggle mode"""
    success: bool
    old_mode: str
    new_mode: str


class ChatMessageResponse(BaseModel):
    """Response model for chat message"""
    success: bool
    response: str
    specs_extracted: int
    conflicts_detected: bool
    suggested_next_question: Optional[str]
    maturity_score: int


class SessionModeResponse(BaseModel):
    """Response model for get mode"""
    success: bool
    mode: str
    session_id: str
    project_id: str


@router.post("/{session_id}/toggle-mode", response_model=ToggleModeResponse)
async def toggle_session_mode(
    session_id: UUID4,
    request: ToggleModeRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Toggle session mode between socratic and direct_chat.

    Args:
        session_id: UUID of the session
        request: Mode to switch to ('socratic' or 'direct_chat')
        current_user: Authenticated user
        orchestrator: Agent orchestrator

    Returns:
        Old mode and new mode
    """
    result = orchestrator.route_request(
        'direct_chat',
        'toggle_mode',
        {
            'session_id': session_id,
            'mode': request.mode
        }
    )

    if not result['success']:
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to toggle mode')
        )

    return ToggleModeResponse(**result)


@router.post("/{session_id}/message", response_model=ChatMessageResponse)
async def send_chat_message(
    session_id: UUID4,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Send a message in direct chat mode.

    Args:
        session_id: UUID of the session
        request: Chat message
        current_user: Authenticated user
        orchestrator: Agent orchestrator

    Returns:
        Assistant response with extracted specs and suggestions
    """
    # TODO: Verify session belongs to user's project
    # For now, we'll pass user_id and let the agent handle it

    result = orchestrator.route_request(
        'direct_chat',
        'process_chat_message',
        {
            'session_id': session_id,
            'user_id': current_user.id,
            'message': request.message,
            'project_id': None  # Will be loaded from session
        }
    )

    if not result['success']:
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to process message')
        )

    # Get project_id from session for response
    session_result = orchestrator.route_request(
        'direct_chat',
        'get_mode',
        {'session_id': session_id}
    )

    if session_result.get('success'):
        result['project_id'] = session_result['project_id']

    return ChatMessageResponse(**result)


@router.get("/{session_id}/mode", response_model=SessionModeResponse)
async def get_session_mode(
    session_id: UUID4,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Get current session mode.

    Args:
        session_id: UUID of the session
        current_user: Authenticated user
        orchestrator: Agent orchestrator

    Returns:
        Current session mode and project info
    """
    result = orchestrator.route_request(
        'direct_chat',
        'get_mode',
        {'session_id': session_id}
    )

    if not result['success']:
        raise HTTPException(
            status_code=404,
            detail=result.get('error', 'Session not found')
        )

    return SessionModeResponse(**result)
