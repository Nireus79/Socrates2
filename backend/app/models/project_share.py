"""
ProjectShare model for specifications database (socrates_specs).
Represents sharing of a project with a team.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from ..core.database import Base


class ProjectShare(Base):
    """
    ProjectShare model - stores in socrates_specs database.

    Note: This model does NOT inherit from BaseModel because it uses
    shared_at instead of created_at, and doesn't need updated_at.

    Fields:
    - id: UUID primary key
    - project_id: Foreign key to projects table (same database)
    - team_id: References teams.id in socrates_auth database (cross-database, no FK)
    - shared_by: References users.id in socrates_auth database (cross-database, no FK)
    - permission_level: Permission level (read, write, admin)
    - shared_at: Timestamp when project was shared

    Relationships:
    - project: Project that is shared
    """
    __tablename__ = "project_shares"
    __table_args__ = (
        Index('idx_project_shares_project_id', 'project_id'),
        Index('idx_project_shares_team_id', 'team_id'),
        Index('idx_project_shares_permission', 'permission_level'),
        UniqueConstraint('project_id', 'team_id', name='project_shares_unique'),
        CheckConstraint("permission_level IN ('read', 'write', 'admin')", name='project_shares_permission_valid'),
    )

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Primary key (UUID)"
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to projects table"
    )

    team_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="References teams.id in socrates_auth database"
    )

    shared_by = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="References users.id in socrates_auth database"
    )

    permission_level = Column(
        String(20),
        nullable=False,
        comment="Permission level: read, write, admin"
    )

    shared_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when project was shared"
    )

    # Relationships
    # project = relationship("Project", back_populates="shares")

    def to_dict(self, exclude_fields: set = None) -> dict:
        """
        Convert model instance to dictionary.

        Args:
            exclude_fields: Set of field names to exclude

        Returns:
            Dictionary representation of model
        """
        exclude_fields = exclude_fields or set()
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Convert UUID and datetime to string for JSON serialization
                if isinstance(value, uuid.UUID):
                    value = str(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()

                result[column.name] = value

        return result

    def __repr__(self):
        """String representation of project share"""
        return f"<ProjectShare(id={self.id}, project_id={self.project_id}, team_id={self.team_id}, permission={self.permission_level})>"
