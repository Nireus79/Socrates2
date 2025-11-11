"""
APIKey model for authentication database (socrates_auth).
Stores encrypted API keys for various LLM providers per user.
"""
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class APIKey(BaseModel):
    """
    APIKey model - stores in socrates_auth database.

    Stores encrypted API keys for LLM providers (Claude, OpenAI, Gemini, etc.)
    Each user can have one API key per provider.

    Fields:
    - id: UUID (inherited from BaseModel)
    - user_id: Foreign key to users table
    - provider: LLM provider name (claude, openai, gemini, ollama, other)
    - api_key_encrypted: Encrypted API key (AES-256)
    - is_active: Whether API key is currently active
    - created_at: Timestamp (inherited from BaseModel)
    - updated_at: Timestamp (inherited from BaseModel)
    - last_used_at: When the API key was last used

    Relationships:
    - user: User who owns this API key
    """
    __tablename__ = "api_keys"
    __table_args__ = (
        Index('idx_api_keys_user_id', 'user_id'),
        Index('idx_api_keys_provider', 'provider'),
        Index('idx_api_keys_is_active', 'is_active', postgresql_where='is_active = true'),
        UniqueConstraint('user_id', 'provider', name='api_keys_user_provider_unique'),
        CheckConstraint("provider IN ('claude', 'openai', 'gemini', 'ollama', 'other')", name='api_keys_provider_valid'),
    )

    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to users table"
    )

    provider = Column(
        String(50),
        nullable=False,
        comment="LLM provider: claude, openai, gemini, ollama, other"
    )

    api_key_encrypted = Column(
        Text,
        nullable=False,
        comment="Encrypted API key (AES-256)"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default='true',
        comment="Whether API key is active"
    )

    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when API key was last used"
    )

    # Relationships
    # user = relationship("User", backref="api_keys")

    def __repr__(self):
        """String representation of API key"""
        return f"<APIKey(id={self.id}, user_id={self.user_id}, provider={self.provider}, is_active={self.is_active})>"
