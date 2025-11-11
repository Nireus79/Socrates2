"""
Admin role definition model.

Defines admin roles and their associated permissions.
"""
from sqlalchemy import Column, String, Text, Boolean, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class AdminRole(BaseModel):
    """Admin role with specific permissions."""

    __tablename__ = "admin_roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(ARRAY(String(50)), nullable=False, default=list)
    is_system_role = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_admin_role_name", "name"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions or [],
            "is_system_role": self.is_system_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# System roles definition
SYSTEM_ROLES = {
    "super_admin": {
        "description": "Full system access",
        "permissions": [
            "users_view",
            "users_suspend",
            "users_delete",
            "users_impersonate",
            "billing_view",
            "invoices_export",
            "metrics_view",
            "audit_log_view",
            "admin_roles_manage",
        ],
    },
    "billing_admin": {
        "description": "Billing and invoicing",
        "permissions": [
            "users_view",
            "billing_view",
            "invoices_export",
            "metrics_view",
        ],
    },
    "support_admin": {
        "description": "User support operations",
        "permissions": [
            "users_view",
            "users_suspend",
            "users_impersonate",
        ],
    },
    "analytics_admin": {
        "description": "Analytics and reporting",
        "permissions": [
            "users_view",
            "billing_view",
            "metrics_view",
        ],
    },
}
