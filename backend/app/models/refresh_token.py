"""
Refresh token model for JWT token refresh mechanism.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class RefreshToken(BaseModel):
    """
    Refresh token model - stores refresh tokens for users.
    Stored in socrates_auth database.

    Fields:
    - id: UUID (inherited from BaseModel)
    - user_id: UUID of the user
    - token: The refresh token string
    - expires_at: When this refresh token expires
    - created_at: Timestamp (inherited from BaseModel)
    - updated_at: Timestamp (inherited from BaseModel)
    """
    __tablename__ = "refresh_tokens"

    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="UUID of user who owns this token"
    )

    token = Column(
        String(500),
        nullable=False,
        unique=True,
        comment="The refresh token string"
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="When this refresh token expires"
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        """String representation of refresh token"""
        return f"<RefreshToken(user_id={self.user_id}, expires_at={self.expires_at})>"

    def is_valid(self) -> bool:
        """Check if refresh token is still valid"""
        from datetime import datetime, timezone
        # Ensure both datetimes have the same timezone awareness
        now = datetime.now(timezone.utc)
        expires = self.expires_at

        # If expires_at is naive, make it aware using UTC
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        return now < expires
