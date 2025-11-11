"""
Admin user model.

Tracks which users have admin privileges and their assigned role.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class AdminUser(BaseModel):
    """User with admin privileges."""

    __tablename__ = "admin_users"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(PG_UUID(as_uuid=True), ForeignKey("admin_roles.id"), nullable=False, index=True)
    granted_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason = Column(String(255), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_admin_user_id", "user_id"),
        Index("idx_admin_role_id", "role_id"),
        Index("idx_admin_revoked", "revoked_at"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "role_id": str(self.role_id),
            "granted_by_id": str(self.granted_by_id),
            "reason": self.reason,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.revoked_at is None,
        }

    @property
    def is_active(self) -> bool:
        """Check if admin role is still active."""
        return self.revoked_at is None
