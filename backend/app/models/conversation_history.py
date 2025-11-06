"""
ConversationHistory model for storing complete conversation history.
"""
from sqlalchemy import Column, String, Text, BigInteger, ForeignKey, Index, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from ..core.database import Base


class ConversationHistory(Base):
    """
    ConversationHistory model - stores complete conversation history.
    Stored in socrates_specs database.

    NOTE: This model does NOT inherit from BaseModel because:
    - Uses BigInteger autoincrement ID instead of UUID
    - Uses timestamp instead of created_at/updated_at

    Fields:
    - id: BigInteger primary key (autoincrement)
    - session_id: Foreign key to sessions table
    - role: Message role (user, assistant, system)
    - content: The message content
    - message_metadata: Additional metadata as JSON
    - timestamp: When the message was sent
    """
    __tablename__ = "conversation_history"
    __table_args__ = (
        Index('idx_conversation_history_session_id', 'session_id'),
        Index('idx_conversation_history_timestamp', 'timestamp'),
    )

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Primary key (autoincrement)"
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

    message_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional metadata as JSON"
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the message was sent"
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
        from datetime import datetime
        import uuid

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
