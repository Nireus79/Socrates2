"""
Role-Based Access Control (RBAC) service.

Manages admin roles, permissions, and access checks.
"""
import logging
from typing import List, Optional, Set

from sqlalchemy.orm import Session

from ..models.admin_audit_log import AdminAuditLog
from ..models.admin_role import SYSTEM_ROLES, AdminRole
from ..models.admin_user import AdminUser
from ..models.user import User

logger = logging.getLogger(__name__)

# Permission definitions
PERMISSIONS = {
    "users_view": "View user information",
    "users_suspend": "Suspend/activate users",
    "users_delete": "Delete user accounts",
    "users_impersonate": "Impersonate users",
    "billing_view": "View billing and subscription data",
    "invoices_export": "Export invoices",
    "metrics_view": "View analytics metrics",
    "audit_log_view": "View admin audit logs",
    "admin_roles_manage": "Create and manage admin roles",
}


class RBACService:
    """Role-Based Access Control operations."""

    @staticmethod
    def initialize_system_roles(db: Session) -> None:
        """
        Create system roles if they don't exist.

        Args:
            db: Database session
        """
        for role_name, role_info in SYSTEM_ROLES.items():
            existing = db.query(AdminRole).filter(AdminRole.name == role_name).first()
            if not existing:
                role = AdminRole(
                    name=role_name,
                    description=role_info["description"],
                    permissions=role_info["permissions"],
                    is_system_role=True,
                )
                db.add(role)
                logger.info(f"Created system role: {role_name}")

        db.commit()

    @staticmethod
    def has_permission(user_id: str, permission: str, db: Session) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: User ID
            permission: Permission to check
            db: Database session

        Returns:
            True if user has permission, False otherwise
        """
        # Super admin check first
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "super_admin":
            return True

        # Check admin role
        admin_user = db.query(AdminUser).filter(
            AdminUser.user_id == user_id,
            AdminUser.revoked_at.is_(None)
        ).first()

        if not admin_user:
            return False

        role = db.query(AdminRole).filter(AdminRole.id == admin_user.role_id).first()
        if not role:
            return False

        return permission in (role.permissions or [])

    @staticmethod
    def get_permissions(user_id: str, db: Session) -> Set[str]:
        """
        Get all permissions for a user.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Set of permission codes
        """
        permissions = set()

        # Super admin has all permissions
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "super_admin":
            return set(PERMISSIONS.keys())

        # Check admin role
        admin_user = db.query(AdminUser).filter(
            AdminUser.user_id == user_id,
            AdminUser.revoked_at.is_(None)
        ).first()

        if admin_user:
            role = db.query(AdminRole).filter(AdminRole.id == admin_user.role_id).first()
            if role:
                permissions = set(role.permissions or [])

        return permissions

    @staticmethod
    def grant_admin_role(
        user_id: str,
        role_id: str,
        granted_by_id: str,
        reason: Optional[str],
        db: Session,
    ) -> AdminUser:
        """
        Grant admin role to a user.

        Args:
            user_id: User to grant role to
            role_id: Role to grant
            granted_by_id: Admin granting the role
            reason: Reason for granting
            db: Database session

        Returns:
            Created AdminUser

        Raises:
            ValueError: If role doesn't exist
        """
        # Check role exists
        role = db.query(AdminRole).filter(AdminRole.id == role_id).first()
        if not role:
            raise ValueError(f"Role {role_id} not found")

        # Remove any existing admin role
        existing = db.query(AdminUser).filter(
            AdminUser.user_id == user_id,
            AdminUser.revoked_at.is_(None)
        ).first()

        if existing:
            existing.revoked_at = existing.updated_at
            db.add(existing)

        # Create new admin user
        admin_user = AdminUser(
            user_id=user_id,
            role_id=role_id,
            granted_by_id=granted_by_id,
            reason=reason,
        )
        db.add(admin_user)
        db.commit()

        logger.info(f"Granted {role.name} to user {user_id} by {granted_by_id}")

        # Audit log
        RBACService.audit_log(
            admin_id=granted_by_id,
            action="role_granted",
            resource_type="user",
            resource_id=str(user_id),
            details={"role_id": str(role_id), "reason": reason},
            db=db,
        )

        return admin_user

    @staticmethod
    def revoke_admin_role(user_id: str, revoked_by_id: str, db: Session) -> None:
        """
        Revoke admin role from a user.

        Args:
            user_id: User to revoke role from
            revoked_by_id: Admin revoking the role
            db: Database session
        """
        admin_user = db.query(AdminUser).filter(
            AdminUser.user_id == user_id,
            AdminUser.revoked_at.is_(None)
        ).first()

        if admin_user:
            admin_user.revoked_at = admin_user.updated_at
            db.add(admin_user)
            db.commit()

            logger.info(f"Revoked admin role from user {user_id} by {revoked_by_id}")

            # Audit log
            RBACService.audit_log(
                admin_id=revoked_by_id,
                action="role_revoked",
                resource_type="user",
                resource_id=str(user_id),
                db=db,
            )

    @staticmethod
    def audit_log(
        admin_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Session = None,
    ) -> None:
        """
        Log an admin action.

        Args:
            admin_id: Admin user ID
            action: Action type
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details
            ip_address: Client IP address
            user_agent: Client user agent
            db: Database session
        """
        if not db:
            return

        log_entry = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log_entry)
        db.commit()

        logger.info(f"Audit: {admin_id} {action} {resource_type}:{resource_id}")

    @staticmethod
    def get_admin_log(
        admin_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
        db: Session = None,
    ) -> List[AdminAuditLog]:
        """
        Get audit logs with optional filters.

        Args:
            admin_id: Filter by admin ID
            action: Filter by action
            resource_type: Filter by resource type
            limit: Max results
            db: Database session

        Returns:
            List of audit log entries
        """
        if not db:
            return []

        query = db.query(AdminAuditLog)

        if admin_id:
            query = query.filter(AdminAuditLog.admin_id == admin_id)
        if action:
            query = query.filter(AdminAuditLog.action == action)
        if resource_type:
            query = query.filter(AdminAuditLog.resource_type == resource_type)

        return query.order_by(AdminAuditLog.created_at.desc()).limit(limit).all()
