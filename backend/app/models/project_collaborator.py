"""Project collaborator model for tracking project access and roles."""
from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class ProjectCollaborator(BaseModel):
    """
    ProjectCollaborator model - tracks who has access to projects and their roles.
    Stored in socrates_specs database.

    Fields:
    - id: UUID (inherited from BaseModel)
    - project_id: UUID of the project
    - user_id: UUID of the collaborator (from socrates_auth database)
    - role: Access level (viewer, editor, owner)
    - added_by: UUID of user who added this collaborator
    - created_at: When collaborator was added (inherited from BaseModel)
    - updated_at: Last update timestamp (inherited from BaseModel)
    """
    __tablename__ = "project_collaborators"
    __table_args__ = (
        Index('idx_project_collaborators_project_id', 'project_id'),
        Index('idx_project_collaborators_user_id', 'user_id'),
        Index('idx_project_collaborators_role', 'role'),
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="UUID of the project"
    )

    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="UUID of the collaborator user (from socrates_auth database)"
    )

    role = Column(
        String(20),
        nullable=False,
        default='viewer',
        server_default='viewer',
        comment="Collaborator role: viewer (read-only), editor (read/write), owner (full control)"
    )

    added_by = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="UUID of user who added this collaborator"
    )

    def __repr__(self):
        """String representation of collaborator"""
        return f"<ProjectCollaborator(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"
