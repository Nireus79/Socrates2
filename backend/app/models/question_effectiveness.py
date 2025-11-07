"""
QuestionEffectiveness model for tracking question effectiveness per user.
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
import uuid

from ..core.database import Base


class QuestionEffectiveness(Base):
    """
    QuestionEffectiveness model - tracks how effective questions are for each user.
    Stored in socrates_specs database.

    NOTE: Does NOT inherit from BaseModel. Has updated_at but no created_at.

    Fields:
    - id: UUID primary key
    - user_id: References users(id) in socrates_auth
    - question_template_id: Question template identifier
    - role: User role (PM, BA, UX, etc.)
    - times_asked: Number of times question was asked
    - times_answered_well: Number of times answered well
    - average_answer_length: Average length of answers
    - average_spec_extraction_count: Average specs extracted per answer
    - effectiveness_score: How effective question is for this user (0.00-1.00)
    - last_asked_at: Last time question was asked
    - updated_at: Timestamp when record was last updated
    """
    __tablename__ = "question_effectiveness"
    __table_args__ = (
        Index('idx_question_effectiveness_user_id', 'user_id'),
        Index('idx_question_effectiveness_role', 'role'),
        Index('idx_question_effectiveness_score', 'effectiveness_score'),
        CheckConstraint('effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 1)', name='question_effectiveness_score_range'),
        UniqueConstraint('user_id', 'question_template_id', name='question_effectiveness_unique'),
    )

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="References users(id) in socrates_auth"
    )

    question_template_id = Column(
        String(100),
        nullable=False,
        comment="Question template identifier"
    )

    role = Column(
        String(50),
        nullable=False,
        comment="User role: PM, BA, UX, Developer, etc."
    )

    times_asked = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times question was asked"
    )

    times_answered_well = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times answered well"
    )

    average_answer_length = Column(
        Integer,
        nullable=True,
        comment="Average length of answers"
    )

    average_spec_extraction_count = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Average specs extracted per answer"
    )

    effectiveness_score = Column(
        Numeric(3, 2),
        nullable=True,
        comment="How effective question is for this user (0.00-1.00)"
    )

    last_asked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time question was asked"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Timestamp when record was last updated"
    )

    def to_dict(self) -> dict:
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'question_template_id': self.question_template_id,
            'role': self.role,
            'times_asked': self.times_asked,
            'times_answered_well': self.times_answered_well,
            'average_answer_length': self.average_answer_length,
            'average_spec_extraction_count': float(self.average_spec_extraction_count) if self.average_spec_extraction_count else None,
            'effectiveness_score': float(self.effectiveness_score) if self.effectiveness_score else None,
            'last_asked_at': self.last_asked_at.isoformat() if self.last_asked_at else None,
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        """String representation of question effectiveness"""
        return f"<QuestionEffectiveness(id={self.id}, user={self.user_id}, template={self.question_template_id}, score={self.effectiveness_score})>"
