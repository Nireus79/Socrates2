"""
UserBehaviorPattern model for learned user behavior patterns.
"""
from sqlalchemy import Column, String, Numeric, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY
from datetime import datetime
import uuid

from ..core.database import Base


class UserBehaviorPattern(Base):
    """
    UserBehaviorPattern model - learned user behavior patterns.
    Stored in socrates_specs database.

    NOTE: Does NOT inherit from BaseModel. Has learned_at and updated_at instead of created_at.

    Fields:
    - id: UUID primary key
    - user_id: References users(id) in socrates_auth
    - pattern_type: Type of pattern (communication_style, detail_level, etc.)
    - pattern_data: Pattern data as JSON
    - confidence: Confidence score (0.00-1.00)
    - learned_from_projects: Array of project UUIDs where pattern was learned
    - learned_at: Timestamp when pattern was learned
    - updated_at: Timestamp when pattern was last updated
    """
    __tablename__ = "user_behavior_patterns"
    __table_args__ = (
        Index('idx_user_behavior_patterns_user_id', 'user_id'),
        Index('idx_user_behavior_patterns_type', 'pattern_type'),
        Index('idx_user_behavior_patterns_confidence', 'confidence'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='user_behavior_patterns_confidence_range'),
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

    pattern_type = Column(
        String(50),
        nullable=False,
        comment="Pattern type: communication_style, detail_level, response_length_preference, etc."
    )

    pattern_data = Column(
        JSONB,
        nullable=False,
        comment="Pattern data as JSON"
    )

    confidence = Column(
        Numeric(3, 2),
        nullable=False,
        comment="Confidence score (0.00-1.00)"
    )

    learned_from_projects = Column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=True,
        comment="Array of project UUIDs where pattern was learned"
    )

    learned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,  # TODO datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
        comment="Timestamp when pattern was learned"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,  # TODO datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
        onupdate=datetime.utcnow,  # TODO datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
        comment="Timestamp when pattern was last updated"
    )

    def to_dict(self) -> dict:
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'pattern_type': self.pattern_type,
            'pattern_data': self.pattern_data,
            'confidence': float(self.confidence),  # TODO Expected type 'str | Buffer | SupportsFloat | SupportsIndex', got 'Column[Decimal]' instead
            'learned_from_projects': [str(p) for p in self.learned_from_projects] if self.learned_from_projects else [],
            'learned_at': self.learned_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        """String representation of user behavior pattern"""
        return f"<UserBehaviorPattern(id={self.id}, user_id={self.user_id}, type={self.pattern_type}, confidence={self.confidence})>"
