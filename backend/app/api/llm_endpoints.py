"""
LLM API endpoints.

Provides:
- List available LLM models
- Get/set current LLM selection
- Manage API keys
- Get usage statistics
- Get cost information
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.llm_router import get_llm_router
from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


class AddAPIKeyRequest(BaseModel):
    """Request model for adding an API key."""
    provider: str  # claude, openai, gemini, ollama, other
    api_key: str


@router.get("/available")
def list_available_models(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List all available LLM models grouped by provider.

    Returns all available LLM providers and their models with pricing and capabilities.

    Example:
        GET /api/v1/llm/available
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "providers": {
                    "anthropic": [
                        {
                            "name": "claude-3.5-sonnet",
                            "description": "Latest Claude model",
                            "context_window": 200000,
                            "max_output_tokens": 4096,
                            "cost_per_1k_input": 0.003,
                            "cost_per_1k_output": 0.015,
                            "capabilities": ["text", "vision", "code", "analysis"]
                        },
                        ...
                    ],
                    "openai": [...],
                    ...
                }
            }
        }
    """
    llm_router = get_llm_router()
    models = llm_router.get_available_models()

    return {
        "success": True,
        "data": {
            "providers": models
        }
    }


@router.get("/current")
def get_current_model(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get currently selected LLM model for the user.

    Returns the user's currently selected LLM provider and model.

    Example:
        GET /api/v1/llm/current
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "provider": "anthropic",
                "model": "claude-3.5-sonnet",
                "description": "Latest Claude model",
                "context_window": 200000,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015,
                "selected_at": "2025-11-13T12:00:00Z"
            }
        }
    """
    llm_router = get_llm_router()
    return llm_router.get_user_model(current_user.id)


class SelectLLMRequest(BaseModel):
    """Request model for selecting LLM provider and model"""
    provider: str
    model: str


@router.post("/select")
def select_model(
    request: SelectLLMRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Select LLM provider and model for the user.

    Allows user to choose which LLM provider and model to use for future interactions.

    Example:
        POST /api/v1/llm/select
        Authorization: Bearer <token>
        {
            "provider": "anthropic",
            "model": "claude-3.5-sonnet"
        }

        Response:
        {
            "success": true,
            "message": "Selected anthropic claude-3.5-sonnet",
            "data": {
                "provider": "anthropic",
                "model": "claude-3.5-sonnet",
                "selected_at": "2025-11-13T12:00:00Z"
            }
        }
    """
    llm_router = get_llm_router()
    return llm_router.set_user_model(current_user.id, request.provider, request.model)


@router.get("/costs")
def get_llm_costs(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get LLM pricing information.

    Returns cost information for all available models.

    Example:
        GET /api/v1/llm/costs
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "providers": {
                    "anthropic": [
                        {
                            "name": "claude-3.5-sonnet",
                            "input_cost_per_1k": 0.003,
                            "output_cost_per_1k": 0.015,
                            "context_window": 200000
                        },
                        ...
                    ],
                    ...
                },
                "comparison": {
                    "anthropic": 3.0,
                    "openai": 4.5,
                    "google": 0.075
                }
            }
        }
    """
    llm_router = get_llm_router()
    return llm_router.get_costs()


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
    period: str = "month",
    current_user: User = Depends(get_current_active_user),
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get LLM usage statistics for the user.

    Returns usage statistics including token counts, costs, and breakdown by model/provider.

    Args:
        period: Time period for statistics (month, week, day)
        current_user: Authenticated user
        db_auth: Auth database session
        db_specs: Specs database session

    Example:
        GET /api/v1/llm/usage
        GET /api/v1/llm/usage?period=week
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "period": "month",
                "overall": {
                    "total_tokens": 15000,
                    "input_tokens": 5000,
                    "output_tokens": 10000,
                    "total_cost": 0.45,
                    "request_count": 10
                },
                "by_model": {
                    "anthropic/claude-3.5-sonnet": {
                        "tokens": 15000,
                        "input_tokens": 5000,
                        "output_tokens": 10000,
                        "cost": 0.45,
                        "calls": 10
                    }
                },
                "by_provider": {
                    "anthropic": {
                        "tokens": 15000,
                        "cost": 0.45,
                        "calls": 10
                    }
                }
            }
        }
    """
    llm_router = get_llm_router()
    return llm_router.get_usage_stats(current_user.id, period)


@router.get("/providers")
def list_llm_providers(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List all available LLM providers and their information.

    This is an alternative endpoint to /available for listing LLM providers.

    Returns all available LLM providers with their models, capabilities, and pricing.

    Example:
        GET /api/v1/llm/providers
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "providers": {
                    "anthropic": [
                        {
                            "name": "claude-3.5-sonnet",
                            "description": "Latest Claude model",
                            "context_window": 200000,
                            "max_output_tokens": 4096,
                            "cost_per_1k_input": 0.003,
                            "cost_per_1k_output": 0.015,
                            "capabilities": ["text", "vision", "code", "analysis"]
                        }
                    ],
                    "openai": [...],
                    "google": [...]
                }
            }
        }
    """
    llm_router = get_llm_router()
    models = llm_router.get_available_models()

    return {
        "success": True,
        "data": {
            "providers": models
        }
    }
