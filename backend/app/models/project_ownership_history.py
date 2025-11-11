"""Project ownership history model for audit trail of ownership transfers."""
from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class ProjectOwnershipHistory(BaseModel):
    """
    ProjectOwnershipHistory model - audit trail of project ownership transfers.
    Stored in socrates_specs database.

    Fields:
    - id: UUID (inherited from BaseModel)
    - project_id: UUID of the project
    - from_user_id: UUID of previous owner (None if initial creation)
    - to_user_id: UUID of new owner
    - transferred_by: UUID of user who authorized the transfer
    - reason: Optional reason for the transfer
    - created_at: When transfer occurred (inherited from BaseModel)
    - updated_at: Last update timestamp (inherited from BaseModel)
    """
    __tablename__ = "project_ownership_history"
    __table_args__ = (
        Index('idx_project_ownership_history_project_id', 'project_id'),
        Index('idx_project_ownership_history_from_user_id', 'from_user_id'),
        Index('idx_project_ownership_history_to_user_id', 'to_user_id'),
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="UUID of the project"
    )

    from_user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="UUID of previous owner (None if initial creation)"
    )

    to_user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="UUID of new owner"
    )

    transferred_by = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="UUID of user who authorized/performed the transfer"
    )

    reason = Column(
        String(255),
        nullable=True,
        comment="Optional reason for the ownership transfer"
    )

    def __repr__(self):
        """String representation of ownership transfer"""
        return f"<ProjectOwnershipHistory(project_id={self.project_id}, from={self.from_user_id}, to={self.to_user_id})>"
