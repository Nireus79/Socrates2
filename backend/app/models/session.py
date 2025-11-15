"""
Session model for chat sessions within projects.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Session(BaseModel):
    """
    Session model - stores chat sessions within projects.
    Stored in socrates_specs database.

    Fields:
    - id: UUID (inherited from BaseModel)
    - project_id: Foreign key to projects table
    - mode: Chat mode (socratic, direct_chat)
    - status: Session status (active, paused, completed)
    - started_at: When the session started
    - ended_at: When the session ended (NULL if still active)
    - created_at: Timestamp (inherited from BaseModel)
    - updated_at: Timestamp (inherited from BaseModel)
    """
    __tablename__ = "sessions"
    __table_args__ = (
        Index('idx_sessions_project_id', 'project_id'),
        Index('idx_sessions_status', 'status'),
        Index('idx_sessions_mode', 'mode'),
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to projects table"
    )

    mode = Column(
        String(20),
        nullable=False,
        default='socratic',
        server_default='socratic',
        comment="Chat mode: socratic, direct_chat"
    )

    status = Column(
        String(20),
        nullable=False,
        default='active',
        server_default='active',
        comment="Session status: active, paused, completed"
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the session started"
    )

    ended_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the session ended (NULL if still active)"
    )

    # Relationships
    project = relationship("Project", back_populates="sessions")
    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")
    # TODO: Enable when Specification.session_id column is created in database
    # specifications = relationship("Specification", back_populates="session")
    conversation_history = relationship("ConversationHistory", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of session"""
        return f"<Session(id={self.id}, project_id={self.project_id}, mode={self.mode}, status={self.status})>"

    def to_dict(self):
        """Convert session to dictionary"""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "mode": self.mode,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
