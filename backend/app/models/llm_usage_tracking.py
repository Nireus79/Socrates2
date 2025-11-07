"""
LLMUsageTracking model for specifications database (socrates_specs).
Tracks LLM API usage for cost monitoring and analytics.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, BigInteger, Numeric, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from ..core.database import Base


class LLMUsageTracking(Base):
    """
    LLMUsageTracking model - stores in socrates_specs database.

    Note: This model does NOT inherit from BaseModel because it uses
    BigInteger for id (auto-increment) and has timestamp instead of created_at/updated_at.

    Fields:
    - id: BigInteger (auto-increment, primary key)
    - user_id: References users.id in socrates_auth database (cross-database, no FK)
    - project_id: Foreign key to projects table (SET NULL on delete)
    - session_id: Foreign key to sessions table (SET NULL on delete)
    - provider: LLM provider used (claude, openai, etc.)
    - model: Model name
    - tokens_input: Input tokens used
    - tokens_output: Output tokens generated
    - tokens_total: Total tokens used
    - cost_usd: Cost in USD
    - latency_ms: Request latency in milliseconds
    - timestamp: When the LLM call was made

    Relationships:
    - project: Project this usage belongs to (if any)
    - session: Session this usage belongs to (if any)
    """
    __tablename__ = "llm_usage_tracking"
    __table_args__ = (
        Index('idx_llm_usage_user_id', 'user_id'),
        Index('idx_llm_usage_project_id', 'project_id'),
        Index('idx_llm_usage_timestamp', 'timestamp', postgresql_using='btree', postgresql_ops={'timestamp': 'DESC'}),
        Index('idx_llm_usage_provider', 'provider'),
    )

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Primary key (auto-increment)"
    )

    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="References users.id in socrates_auth database"
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('projects.id', ondelete='SET NULL'),
        nullable=True,
        comment="Foreign key to projects table"
    )

    session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('sessions.id', ondelete='SET NULL'),
        nullable=True,
        comment="Foreign key to sessions table"
    )

    provider = Column(
        String(50),
        nullable=False,
        comment="LLM provider used"
    )

    model = Column(
        String(100),
        nullable=False,
        comment="Model name"
    )

    tokens_input = Column(
        Integer,
        nullable=False,
        comment="Input tokens used"
    )

    tokens_output = Column(
        Integer,
        nullable=False,
        comment="Output tokens generated"
    )

    tokens_total = Column(
        Integer,
        nullable=False,
        comment="Total tokens used"
    )

    cost_usd = Column(
        Numeric(precision=10, scale=6),
        nullable=True,
        comment="Cost in USD"
    )

    latency_ms = Column(
        Integer,
        nullable=True,
        comment="Request latency in milliseconds"
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the LLM call was made"
    )

    # Relationships
    # project = relationship("Project", back_populates="llm_usage")
    # session = relationship("Session", back_populates="llm_usage")

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

                # Convert types for JSON serialization
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, Decimal):
                    value = float(value)

                result[column.name] = value

        return result

    def __repr__(self):
        """String representation of LLM usage tracking"""
        return f"<LLMUsageTracking(id={self.id}, provider={self.provider}, model={self.model}, tokens={self.tokens_total}, cost=${self.cost_usd})>"
