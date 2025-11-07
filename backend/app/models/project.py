"""
Project model for user projects.
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Project(BaseModel):
    """
    Project model - stores user projects.
    Stored in socrates_specs database.

    Fields:
    - id: UUID (inherited from BaseModel)
    - user_id: Foreign key to users table (in socrates_auth database)
    - name: Project name
    - description: Project description
    - current_phase: Current workflow phase (discovery, analysis, design, implementation)
    - maturity_score: Overall maturity score (0-100)
    - status: Project status (active, archived, completed)
    - created_at: Timestamp (inherited from BaseModel)
    - updated_at: Timestamp (inherited from BaseModel)
    """
    __tablename__ = "projects"
    __table_args__ = (
        Index('idx_projects_user_id', 'user_id'),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_current_phase', 'current_phase'),
        Index('idx_projects_maturity_score', 'maturity_score'),
    )

    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="Foreign key to users table (in socrates_auth database)"
    )

    name = Column(
        String(255),
        nullable=False,
        comment="Project name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Project description"
    )

    current_phase = Column(
        String(50),
        nullable=False,
        default='discovery',
        server_default='discovery',
        comment="Current workflow phase: discovery, analysis, design, implementation"
    )

    maturity_score = Column(
        Integer,
        nullable=False,
        default=0,
        server_default='0',
        comment="Overall maturity score (0-100)"
    )

    status = Column(
        String(20),
        nullable=False,
        default='active',
        server_default='active',
        comment="Project status: active, archived, completed"
    )

    # Relationships
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="project", cascade="all, delete-orphan")
    specifications = relationship("Specification", back_populates="project", cascade="all, delete-orphan")
    quality_metrics = relationship("QualityMetric", back_populates="project", cascade="all, delete-orphan")
    knowledge_base_documents = relationship("KnowledgeBaseDocument", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of project"""
        return f"<Project(id={self.id}, name='{self.name}', maturity_score={self.maturity_score})>"
