"""
Activity log model for tracking user actions on projects.

Records all significant user activities for audit trails, activity feeds, and analytics.
"""
from sqlalchemy import Column, ForeignKey, Index, JSON, String, Text

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class ActivityLog(BaseModel):
    """
    Activity log model - tracks all user actions on projects.
    Stored in socrates_specs database.

    Logs various actions such as:
    - spec_created, spec_updated, spec_deleted
    - comment_added, comment_updated, comment_deleted
    - document_uploaded, document_deleted
    - collaboration_invite_sent, member_added, member_removed
    - project_created, project_renamed, project_archived

    Fields:
    - id: UUID (inherited from BaseModel)
    - project_id: Foreign key to projects table
    - user_id: References users(id) in socrates_auth
    - action_type: Type of action performed (spec_created, comment_added, etc.)
    - entity_type: Type of entity affected (specification, comment, document, etc.)
    - entity_id: ID of the affected entity (optional, for tracking specific items)
    - description: Human-readable description of the action
    - metadata: Additional context as JSON (before/after values, etc.)
    - created_at: Timestamp (inherited from BaseModel)
    - updated_at: Timestamp (inherited from BaseModel)

    Example:
        ActivityLog(
            project_id="proj_123",
            user_id="user_456",
            action_type="spec_created",
            entity_type="specification",
            entity_id="spec_789",
            description="Created specification: API Rate Limit",
            metadata={
                "category": "performance",
                "key": "api_rate_limit",
                "value": "1000 requests/minute"
            }
        )
    """
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index('idx_activity_logs_project_id', 'project_id'),
        Index('idx_activity_logs_user_id', 'user_id'),
        Index('idx_activity_logs_action_type', 'action_type'),
        Index('idx_activity_logs_entity_type', 'entity_type'),
        Index('idx_activity_logs_created_at', 'created_at'),
        Index('idx_activity_logs_project_created', 'project_id', 'created_at'),
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to projects table"
    )

    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="References users(id) in socrates_auth - who performed the action"
    )

    action_type = Column(
        String(50),
        nullable=False,
        comment="""Action type: spec_created, spec_updated, spec_deleted, comment_added,
                   comment_updated, comment_deleted, document_uploaded, document_deleted,
                   member_added, member_removed, member_role_changed, project_created,
                   project_renamed, project_archived, maturity_updated, conflict_detected,
                   conflict_resolved"""
    )

    entity_type = Column(
        String(50),
        nullable=False,
        comment="""Entity type affected: specification, comment, document, project_member,
                   project, conflict, maturity_metric"""
    )

    entity_id = Column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="ID of the affected entity (optional, for tracking specific items)"
    )

    description = Column(
        Text,
        nullable=False,
        comment="Human-readable description of the action"
    )

    action_metadata = Column(
        JSON,
        nullable=True,
        comment="""Additional context as JSON. Examples:
                   - before/after values for updates
                   - reason for deletion
                   - conflict details
                   - member role changes"""
    )

    # Relationships
    project = relationship("Project", back_populates="activity_logs")

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "user_id": str(self.user_id),
            "action_type": self.action_type,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "description": self.description,
            "metadata": self.action_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """String representation of activity log entry."""
        return f"<ActivityLog(id={self.id}, action={self.action_type}, entity={self.entity_type})>"
