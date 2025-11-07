"""
LLM API endpoints.

Provides:
- List LLM providers
- Manage API keys
- Get usage statistics
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..agents.orchestrator import get_orchestrator

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


class AddAPIKeyRequest(BaseModel):
    """Request model for adding an API key."""
    provider: str  # claude, openai, gemini, ollama, other
    api_key: str


@router.get("/providers")
def list_providers(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List available LLM providers.

    Args:
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'providers': List[dict]
        }

    Example:
        GET /api/v1/llm/providers
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "providers": [
                {
                    "id": "claude",
                    "name": "Anthropic Claude",
                    "models": [...],
                    "requires_api_key": false,
                    ...
                },
                ...
            ]
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='llm',
        action='list_providers',
        data={}
    )

    return result


@router.post("/api-keys")
def add_api_key(
    request: AddAPIKeyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Add or update API key for LLM provider.

    Args:
        request: API key details
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'api_key_id': str,
            'provider': str,
            'action': 'created' | 'updated'
        }

    Example:
        POST /api/v1/llm/api-keys
        Authorization: Bearer <token>
        {
            "provider": "openai",
            "api_key": "sk-..."
        }

        Response:
        {
            "success": true,
            "api_key_id": "abc-123",
            "provider": "openai",
            "action": "created"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='llm',
        action='add_api_key',
        data={
            'user_id': current_user.id,
            'provider': request.provider,
            'api_key': request.api_key
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to add API key')
        )

    return result


@router.get("/usage")
def get_usage_stats(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get LLM usage statistics.

    Args:
        project_id: Optional project ID to filter by
        current_user: Authenticated user
        db_auth: Auth database session
        db_specs: Specs database session

    Returns:
        {
            'success': bool,
            'total_tokens': int,
            'total_cost': float,
            'total_calls': int,
            'usage_by_provider': dict
        }

    Example:
        GET /api/v1/llm/usage
        GET /api/v1/llm/usage?project_id=abc-123
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "total_tokens": 15000,
            "total_cost": 0.45,
            "total_calls": 10,
            "usage_by_provider": {
                "claude": {
                    "tokens_input": 5000,
                    "tokens_output": 10000,
                    "tokens_total": 15000,
                    "cost": 0.45,
                    "calls": 10,
                    "avg_latency_ms": 1500
                }
            }
        }
    """
    orchestrator = get_orchestrator()

    data = {'user_id': current_user.id}
    if project_id:
        data['project_id'] = project_id

    result = orchestrator.route_request(
        agent_id='llm',
        action='get_usage_stats',
        data=data
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to get usage stats')
        )

    return result
