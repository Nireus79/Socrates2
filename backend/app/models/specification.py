"""
Specification model for extracted project specifications.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, JSON, Numeric, String, Text

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Specification(BaseModel):
    """
    Specification model - stores extracted specifications from conversations.
    Stored in socrates_specs database.

    Structured as key-value pairs (compatible with socrates-ai library format):
    - key: Identifier for the specification (e.g., "api_framework")
    - value: The actual specification value (e.g., "FastAPI")
    - content: Optional detailed notes or context (for complex specifications)

    Fields:
    - id: UUID (inherited from BaseModel)
    - project_id: Foreign key to projects table
    - session_id: Foreign key to sessions table (can be NULL)
    - category: Specification category (goals, requirements, tech_stack, etc.)
    - key: Specification identifier (e.g., "api_framework") - REQUIRED
    - value: Specification value (e.g., "FastAPI") - REQUIRED
    - content: Full specification content or detailed notes (for complex specs)
    - source: Source of spec (user_input, extracted, inferred)
    - confidence: Confidence score (0.00-1.00)
    - is_current: Whether this is the current version (superseded specs have false)
    - spec_metadata: Additional metadata as JSON
    - superseded_at: Timestamp when this spec was superseded
    - superseded_by: ID of the specification that superseded this one
    - created_at: Timestamp (inherited from BaseModel)
    - updated_at: Timestamp (inherited from BaseModel)

    Example:
        Specification(
            category='tech_stack',
            key='api_framework',
            value='FastAPI',
            content='FastAPI web framework for async APIs',
            confidence=0.95,
            source='user_input'
        )
    """
    __tablename__ = "specifications"
    __table_args__ = (
        Index('idx_specifications_project_id', 'project_id'),
        Index('idx_specifications_category', 'category'),
        Index('idx_specifications_is_current', 'is_current', postgresql_where=Column('is_current') == True),
        Index('idx_specifications_created_at', 'created_at'),
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to projects table"
    )

    # TODO: Enable when session_id column is created in database migration
    # session_id = Column(
    #     PG_UUID(as_uuid=True),
    #     ForeignKey('sessions.id', ondelete='SET NULL'),
    #     nullable=True,
    #     comment="Foreign key to sessions table (can be NULL)"
    # )

    category = Column(
        String(100),
        nullable=False,
        comment="Specification category: goals, requirements, tech_stack, scalability, security, performance, testing, monitoring, data_retention, disaster_recovery"
    )

    key = Column(
        String(255),
        nullable=False,
        comment="Specification identifier/name (e.g., 'api_framework', 'database', 'authentication'). Part of key-value pair structure."
    )

    value = Column(
        Text,
        nullable=False,
        comment="Specification value (e.g., 'FastAPI', 'PostgreSQL', 'JWT'). Part of key-value pair structure."
    )

    content = Column(
        Text,
        nullable=True,
        comment="Full specification content or detailed notes (optional, for complex specifications). Kept for backward compatibility."
    )

    source = Column(
        String(50),
        nullable=False,
        comment="Source of specification: user_input, extracted, inferred"
    )

    confidence = Column(
        Numeric(3, 2),
        nullable=True,
        comment="Confidence score (0.00-1.00)"
    )

    is_current = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default='true',
        comment="Whether this is the current version (superseded specs have false)"
    )

    spec_metadata = Column(
        JSON,
        nullable=True,
        comment="Additional metadata as JSON"
    )

    superseded_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when this spec was superseded"
    )

    superseded_by = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('specifications.id', ondelete='SET NULL'),
        nullable=True,
        comment="ID of the specification that superseded this one"
    )

    # Relationships
    project = relationship("Project", back_populates="specifications")
    # TODO: Enable when session_id column is created in database
    # session = relationship("Session", back_populates="specifications")

    def __repr__(self):
        """String representation of specification"""
        return f"<Specification(id={self.id}, category={self.category}, content='{self.content[:50]}...')>"
