"""
Admin API endpoints.

Provides:
- Health check
- System statistics
- Agent information
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any

from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_admin_user
from ..models.user import User
from ..agents.orchestrator import get_orchestrator

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/health")
def health_check(
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Health check endpoint.

    Verifies:
    - API is running
    - Auth database is connected
    - Specs database is connected

    Returns:
        Dictionary with health status

    Example:
        GET /api/v1/admin/health

        Response:
        {
            "status": "healthy",
            "databases": {
                "auth": "connected",
                "specs": "connected"
            }
        }
    """
    # Test auth database connection
    try:
        db_auth.execute(text("SELECT 1"))
        auth_status = "connected"
    except Exception as e:
        auth_status = f"error: {str(e)}"

    # Test specs database connection
    try:
        db_specs.execute(text("SELECT 1"))
        specs_status = "connected"
    except Exception as e:
        specs_status = f"error: {str(e)}"

    # Overall status
    overall_status = "healthy" if (
        auth_status == "connected" and specs_status == "connected"
    ) else "unhealthy"

    return {
        "status": overall_status,
        "databases": {
            "auth": auth_status,
            "specs": specs_status
        }
    }


@router.get("/stats")
def get_stats(
    current_user: User = Depends(get_current_admin_user),
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get system statistics.
    Requires admin role.

    Returns:
        Dictionary with:
        - User counts
        - Project counts
        - Session counts
        - Agent statistics

    Example:
        GET /api/v1/admin/stats
        Authorization: Bearer <admin_token>

        Response:
        {
            "users": {
                "total": 42,
                "active": 38,
                "verified": 35
            },
            "projects": {
                "total": 156,
                "active": 142
            },
            "sessions": {
                "total": 489,
                "active": 12
            },
            "agents": {
                "total_agents": 3,
                "total_requests": 1234,
                "agents": [...]
            }
        }
    """
    # Get user counts from auth database
    from ..models.user import User as UserModel

    total_users = db_auth.query(UserModel).count()
    active_users = db_auth.query(UserModel).filter(
        UserModel.is_active == True
    ).count()
    verified_users = db_auth.query(UserModel).filter(
        UserModel.is_verified == True
    ).count()

    # Get orchestrator statistics
    orchestrator = get_orchestrator()
    agent_stats = orchestrator.get_stats()

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users
        },
        "agents": agent_stats
    }


@router.get("/agents")
def get_agents(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get information about all registered agents.
    Requires admin role.

    Returns:
        Dictionary with agent information

    Example:
        GET /api/v1/admin/agents
        Authorization: Bearer <admin_token>

        Response:
        {
            "total_agents": 3,
            "agents": [
                {
                    "agent_id": "project_manager",
                    "name": "Project Manager Agent",
                    "capabilities": ["create_project", "update_project"],
                    "stats": {...}
                },
                ...
            ]
        }
    """
    orchestrator = get_orchestrator()
    all_agents = orchestrator.get_all_agents()

    return {
        "total_agents": len(all_agents),
        "agents": all_agents
    }
