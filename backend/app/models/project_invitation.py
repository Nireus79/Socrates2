"""
Project invitation model for managing team collaboration requests.
"""
import enum

from sqlalchemy import Column, Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class InvitationStatus(str, enum.Enum):
    """Invitation status enumeration."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ProjectInvitation(BaseModel):
    """
    ProjectInvitation model - tracks project access invitations.
    Stored in socrates_specs database.

    Allows project owners to invite other users to collaborate on projects
    with specific roles and permissions.

    Fields:
    - id: UUID (inherited from BaseModel)
    - project_id: Foreign key to projects table
    - invited_by: UUID of user who sent the invitation
    - invited_email: Email of the invited user
    - invited_user_id: UUID of invited user (if already a Socrates user)
    - role: Role to assign (viewer, editor, owner)
    - status: Invitation status (pending, accepted, declined, expired, revoked)
    - message: Optional personal message from inviter
    - expires_at: When the invitation expires
    - accepted_at: When/if invitation was accepted
    - created_at: When invitation was created (inherited)
    - updated_at: Last update timestamp (inherited)
    """
    __tablename__ = "project_invitations"
    __table_args__ = (
        Index('idx_project_invitations_project_id', 'project_id'),
        Index('idx_project_invitations_invited_email', 'invited_email'),
        Index('idx_project_invitations_invited_user_id', 'invited_user_id'),
        Index('idx_project_invitations_status', 'status'),
        Index('idx_project_invitations_created_at', 'created_at'),
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="Foreign key to projects table"
    )

    invited_by = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="UUID of user who sent the invitation"
    )

    invited_email = Column(
        String(255),
        nullable=False,
        comment="Email address of the invited user"
    )

    invited_user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="UUID of invited user if already a Socrates user"
    )

    role = Column(
        String(20),
        nullable=False,
        default="editor",
        comment="Role to assign: viewer (read), editor (read/write), owner (full control)"
    )

    status = Column(
        Enum(InvitationStatus),
        nullable=False,
        default=InvitationStatus.PENDING,
        comment="Invitation status: pending, accepted, declined, expired, revoked"
    )

    message = Column(
        Text,
        nullable=True,
        comment="Optional personal message from inviter"
    )

    expires_at = Column(
        String(50),  # ISO format timestamp
        nullable=True,
        comment="When the invitation expires (ISO 8601 format)"
    )

    accepted_at = Column(
        String(50),  # ISO format timestamp
        nullable=True,
        comment="When the invitation was accepted (ISO 8601 format)"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "invited_by": str(self.invited_by),
            "invited_email": self.invited_email,
            "invited_user_id": str(self.invited_user_id) if self.invited_user_id else None,
            "role": self.role,
            "status": self.status.value,
            "message": self.message,
            "expires_at": self.expires_at,
            "accepted_at": self.accepted_at,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """String representation of project invitation."""
        return f"<ProjectInvitation(project_id={self.project_id}, invited_email={self.invited_email}, status={self.status})>"
