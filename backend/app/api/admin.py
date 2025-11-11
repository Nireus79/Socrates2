"""
Admin API endpoints.

Provides:
- Health check
- System statistics
- Agent information
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..agents.orchestrator import get_orchestrator
from ..core.action_logger import is_action_logging_enabled, toggle_action_logging
from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_admin_user
from ..models.admin_role import AdminRole
from ..models.admin_user import AdminUser
from ..models.user import User
from ..services.analytics_service import AnalyticsService
from ..services.rbac_service import RBACService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class ActionLoggingToggleRequest(BaseModel):
    """Request to toggle action logging."""
    enabled: bool


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


@router.post("/logging/action")
def toggle_action_logging_endpoint(
    request: ActionLoggingToggleRequest,
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Toggle action logging on/off at runtime.

    This allows administrators to enable/disable comprehensive action logging
    without restarting the server. Useful for reducing log volume in production
    while keeping it available when debugging issues.

    Args:
        request: Toggle request with enabled flag
        current_user: Must be admin user

    Returns:
        New logging state

    Example:
        POST /api/v1/admin/logging/action
        Authorization: Bearer <admin_token>
        {
            "enabled": true
        }

        Response:
        {
            "success": true,
            "enabled": true,
            "message": "Action logging enabled"
        }
    """
    new_state = toggle_action_logging(request.enabled)

    return {
        "success": True,
        "enabled": new_state,
        "message": f"Action logging {'enabled' if new_state else 'disabled'}"
    }


@router.get("/logging/action")
def get_action_logging_status(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get current action logging status.

    Args:
        current_user: Must be admin user

    Returns:
        Current logging state

    Example:
        GET /api/v1/admin/logging/action
        Authorization: Bearer <admin_token>

        Response:
        {
            "enabled": true,
            "message": "Action logging is currently enabled"
        }
    """
    enabled = is_action_logging_enabled()

    return {
        "enabled": enabled,
        "message": f"Action logging is currently {'enabled' if enabled else 'disabled'}"
    }


# ===== Response Models =====

class AdminRoleResponse(BaseModel):
    """Admin role response model."""
    id: str
    name: str
    description: str
    permissions: List[str]
    is_system_role: bool
    users_count: int


class AdminUserResponse(BaseModel):
    """Admin user response model."""
    id: str
    user_id: str
    user_email: str
    role_name: str
    granted_at: str
    granted_by_email: Optional[str]
    reason: Optional[str]
    is_active: bool


class AuditLogResponse(BaseModel):
    """Audit log entry response model."""
    id: str
    admin_email: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    created_at: str


class MetricsResponse(BaseModel):
    """Metrics data response model."""
    dau: Optional[Dict[str, Any]]
    mrr: Optional[Dict[str, Any]]
    churn: Optional[Dict[str, Any]]
    funnel: Optional[Dict[str, Any]]


class UserSearchResponse(BaseModel):
    """User search result response model."""
    id: str
    email: str
    name: Optional[str]
    is_active: bool
    is_verified: bool
    subscription_tier: str
    created_at: str
    last_login: Optional[str]
    admin_role: Optional[str]


# ===== Helper Functions =====

def require_permission(permission: str):
    """
    Dependency to check if user has specific permission.

    Args:
        permission: Required permission name

    Returns:
        Dependency function
    """
    async def check_permission(current_user: User = Depends(get_current_admin_user)) -> User:
        if not RBACService.has_permission(current_user.id, permission):
            raise HTTPException(
                status_code=403,
                detail=f"User does not have '{permission}' permission"
            )
        return current_user

    return check_permission


# ===== Admin Roles Endpoints =====

@router.get("/roles", response_model=List[AdminRoleResponse])
def list_admin_roles(
    current_user: User = Depends(require_permission("roles_view")),
    db: Session = Depends(get_db_auth)
) -> List[AdminRoleResponse]:
    """
    List all admin roles.
    Requires 'roles_view' permission.

    Returns:
        List of admin roles with user counts
    """
    from sqlalchemy import func

    from ..models.admin_user import AdminUser

    # Get all roles
    roles = db.query(AdminRole).all()

    # Single query to get user counts for all roles
    role_user_counts = db.query(
        AdminUser.role_id,
        func.count(AdminUser.id).label('users_count')
    ).filter(
        AdminUser.revoked_at.is_(None)
    ).group_by(AdminUser.role_id).all()

    # Build a map of role_id -> count
    count_map = {role_id: count for role_id, count in role_user_counts}

    result = []
    for role in roles:
        users_count = count_map.get(role.id, 0)

        result.append(AdminRoleResponse(
            id=str(role.id),
            name=role.name,
            description=role.description,
            permissions=role.permissions,
            is_system_role=role.is_system_role,
            users_count=users_count
        ))

    return result


@router.get("/roles/{role_id}", response_model=AdminRoleResponse)
def get_admin_role(
    role_id: str,
    current_user: User = Depends(require_permission("roles_view")),
    db: Session = Depends(get_db_auth)
) -> AdminRoleResponse:
    """
    Get specific admin role details.
    Requires 'roles_view' permission.

    Args:
        role_id: Role ID

    Returns:
        Admin role details
    """
    from ..models.admin_user import AdminUser

    role = db.query(AdminRole).filter(AdminRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    users_count = db.query(AdminUser).filter(
        AdminUser.role_id == role.id,
        AdminUser.revoked_at.is_(None)
    ).count()

    return AdminRoleResponse(
        id=str(role.id),
        name=role.name,
        description=role.description,
        permissions=role.permissions,
        is_system_role=role.is_system_role,
        users_count=users_count
    )


# ===== Admin Users Endpoints =====

@router.get("/users", response_model=List[AdminUserResponse])
def list_admin_users(
    role_id: Optional[str] = None,
    current_user: User = Depends(require_permission("users_view")),
    db: Session = Depends(get_db_auth)
) -> List[AdminUserResponse]:
    """
    List all admin users.
    Requires 'users_view' permission.

    Args:
        role_id: Optional role filter

    Returns:
        List of admin users
    """
    from sqlalchemy.orm import joinedload

    from ..models.admin_user import AdminUser

    query = db.query(AdminUser).filter(
        AdminUser.revoked_at.is_(None)
    ).options(
        joinedload(AdminUser.role),
        joinedload(AdminUser.user),
        joinedload(AdminUser.granted_by_user)
    )

    if role_id:
        query = query.filter(AdminUser.role_id == role_id)

    admin_users = query.all()
    result = []

    for admin_user in admin_users:
        result.append(AdminUserResponse(
            id=str(admin_user.id),
            user_id=str(admin_user.user_id),
            user_email=admin_user.user.email if admin_user.user else "Unknown",
            role_name=admin_user.role.name if admin_user.role else "Unknown",
            granted_at=admin_user.created_at.isoformat(),
            granted_by_email=admin_user.granted_by_user.email if admin_user.granted_by_user else None,
            reason=admin_user.reason,
            is_active=admin_user.is_active
        ))

    return result


@router.post("/users/{user_id}/grant-role")
def grant_admin_role(
    user_id: str,
    role_id: str = Query(..., description="Role ID to grant"),
    reason: Optional[str] = Query(None, description="Reason for granting"),
    current_user: User = Depends(require_permission("users_manage")),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Grant admin role to user.
    Requires 'users_manage' permission.

    Args:
        user_id: User ID
        role_id: Role ID to grant
        reason: Optional reason for granting

    Returns:
        Success response
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    RBACService.grant_admin_role(
        user_id=user_id,
        role_id=role_id,
        granted_by_id=str(current_user.id),
        reason=reason,
        db=db
    )

    logger.info(f"Admin {current_user.id} granted role {role_id} to user {user_id}")

    return {
        "status": "success",
        "message": f"Role granted to {target_user.email}",
        "user_id": user_id,
        "role_id": role_id
    }


@router.post("/users/{user_id}/revoke-role")
def revoke_admin_role(
    user_id: str,
    current_user: User = Depends(require_permission("users_manage")),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Revoke admin role from user.
    Requires 'users_manage' permission.

    Args:
        user_id: User ID

    Returns:
        Success response
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    RBACService.revoke_admin_role(user_id=user_id, db=db)

    logger.info(f"Admin {current_user.id} revoked admin role from user {user_id}")

    return {
        "status": "success",
        "message": f"Role revoked from {target_user.email}",
        "user_id": user_id
    }


# ===== User Management Endpoints =====

@router.get("/users/search", response_model=List[UserSearchResponse])
def search_users(
    query: str = Query(..., min_length=1, description="Search query (email, name, or ID)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("users_view")),
    db: Session = Depends(get_db_auth)
) -> List[UserSearchResponse]:
    """
    Search users by email, name, or ID.
    Requires 'users_view' permission.

    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        List of matching users
    """
    from sqlalchemy import or_
    from sqlalchemy.orm import selectinload

    users = db.query(User).filter(
        or_(
            User.email.ilike(f"%{query}%"),
            User.name.ilike(f"%{query}%"),
            User.id == query
        )
    ).options(
        selectinload(User.admin_user).selectinload(AdminUser.role)
    ).limit(limit).all()

    result = []
    for user in users:
        admin_role = None
        if user.admin_user and user.admin_user.revoked_at is None:
            admin_role = user.admin_user.role.name if user.admin_user.role else None

        result.append(UserSearchResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            subscription_tier=user.subscription_tier or "free",
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None,
            admin_role=admin_role
        ))

    return result


@router.post("/users/{user_id}/suspend")
def suspend_user(
    user_id: str,
    reason: Optional[str] = Query(None, description="Suspension reason"),
    current_user: User = Depends(require_permission("users_manage")),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Suspend user account (disable login).
    Requires 'users_manage' permission.

    Args:
        user_id: User ID
        reason: Suspension reason

    Returns:
        Success response
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")

    user.is_active = False
    db.commit()

    RBACService.audit_log(
        admin_id=str(current_user.id),
        action="user_suspended",
        resource_type="user",
        resource_id=user_id,
        details={"reason": reason},
        db=db
    )

    logger.info(f"Admin {current_user.id} suspended user {user_id}")

    return {
        "status": "success",
        "message": f"User {user.email} has been suspended",
        "user_id": user_id
    }


@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: str,
    current_user: User = Depends(require_permission("users_manage")),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Activate suspended user account.
    Requires 'users_manage' permission.

    Args:
        user_id: User ID

    Returns:
        Success response
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()

    RBACService.audit_log(
        admin_id=str(current_user.id),
        action="user_activated",
        resource_type="user",
        resource_id=user_id,
        details={},
        db=db
    )

    logger.info(f"Admin {current_user.id} activated user {user_id}")

    return {
        "status": "success",
        "message": f"User {user.email} has been activated",
        "user_id": user_id
    }


# ===== Analytics Endpoints =====

@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    current_user: User = Depends(require_permission("metrics_view")),
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> MetricsResponse:
    """
    Get current analytics metrics.
    Requires 'metrics_view' permission.

    Returns:
        Current metrics snapshot
    """
    metrics = AnalyticsService.get_current_metrics(db_auth, db_specs)

    return MetricsResponse(**metrics)


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_permission("audit_logs_view")),
    db: Session = Depends(get_db_auth)
) -> List[AuditLogResponse]:
    """
    Get audit logs with optional filtering.
    Requires 'audit_logs_view' permission.

    Args:
        action: Filter by action type
        resource_type: Filter by resource type
        limit: Maximum results
        offset: Result offset for pagination

    Returns:
        List of audit log entries
    """
    logs = RBACService.get_admin_log(
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
        db=db
    )

    result = []
    for log in logs:
        admin_user = db.query(User).filter(User.id == log.admin_id).first()

        result.append(AuditLogResponse(
            id=str(log.id),
            admin_email=admin_user.email if admin_user else "Unknown",
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details or {},
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat()
        ))

    return result


@router.get("/metrics/export")
async def export_metrics(
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(require_permission("metrics_export")),
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Export metrics in specified format.
    Requires 'metrics_export' permission.

    Args:
        format: Export format (json or csv)

    Returns:
        Metrics data
    """

    metrics = AnalyticsService.get_current_metrics(db_auth, db_specs)

    RBACService.audit_log(
        admin_id=str(current_user.id),
        action="metrics_exported",
        resource_type="metrics",
        resource_id=None,
        details={"format": format},
        db=db_auth
    )

    logger.info(f"Admin {current_user.id} exported metrics in {format} format")

    return {
        "status": "success",
        "format": format,
        "data": metrics,
        "exported_at": datetime.now(timezone.utc).isoformat()
    }
