"""
ConversationHistory model for storing complete conversation history.
"""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, JSON, String, Text, func

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class ConversationHistory(Base):
    """
    ConversationHistory model - stores complete conversation history.
    Stored in socrates_specs database.

    Fields match the database schema created in migration 003:
    - id: UUID primary key
    - session_id: Foreign key to sessions table
    - role: Message role (user, assistant, system)
    - content: The message content
    - message_type: Type of message (question, answer, clarification, specification, error)
    - tokens_used: Number of tokens used in LLM response
    - metadata: Additional metadata as JSONB
    - created_at: When the message was created
    """
    __tablename__ = "conversation_history"
    __table_args__ = (
        Index('idx_conversation_history_session_id', 'session_id'),
        Index('idx_conversation_history_created_at', 'created_at'),
    )

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.text('gen_random_uuid()'),
        comment="Unique message identifier (UUID)"
    )

    session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('sessions.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to sessions table"
    )

    role = Column(
        String(20),
        nullable=False,
        comment="Message role: user, assistant, system"
    )

    content = Column(
        Text,
        nullable=False,
        comment="The message content"
    )

    message_type = Column(
        String(50),
        nullable=True,
        comment="Message type (question, answer, clarification, specification, error)"
    )

    tokens_used = Column(
        Integer,
        nullable=True,
        comment="Number of tokens used in LLM response"
    )

    metadata = Column(
        JSON,
        nullable=True,
        comment="Additional metadata as JSON"
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the message was created"
    )

    # Relationships
    session = relationship("Session", back_populates="conversation_history")

    def to_dict(self, exclude_fields: set = None) -> dict:
        """
        Convert model instance to dictionary.

        Args:
            exclude_fields: Set of field names to exclude

        Returns:
            Dictionary representation of model
        """
        import uuid
        from datetime import datetime

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
        """String representation of conversation message"""
        return f"<ConversationHistory(id={self.id}, role={self.role}, content='{self.content[:50]}...')>"
