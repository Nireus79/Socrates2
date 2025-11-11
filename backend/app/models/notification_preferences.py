"""Notification preference model.

Stores user notification preferences for different event types
and delivery methods.
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime, timezone
from .base import BaseModel


class NotificationPreferences(BaseModel):
    """User notification preferences.

    Allows users to control which notifications they receive and
    how frequently they want to be notified.

    Attributes:
        id: Unique identifier
        user_id: Foreign key to users table
        email_on_conflict: Send email on specification conflict detection
        email_on_maturity: Send email on project maturity milestones
        email_on_mention: Send email when mentioned in comments
        email_on_activity: Send email on team activity
        digest_frequency: How often to send digest emails (real_time, daily, weekly, off)
        created_at: Timestamp when preferences were created
        updated_at: Timestamp when preferences were last updated
    """
    __tablename__ = "notification_preferences"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, unique=True, index=True)

    # Email notification toggles
    email_on_conflict = Column(Boolean, default=True)
    email_on_maturity = Column(Boolean, default=True)
    email_on_mention = Column(Boolean, default=True)
    email_on_activity = Column(Boolean, default=False)

    # Digest frequency: real_time, daily, weekly, off
    digest_frequency = Column(String(20), default="daily")

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "email_on_conflict": self.email_on_conflict,
            "email_on_maturity": self.email_on_maturity,
            "email_on_mention": self.email_on_mention,
            "email_on_activity": self.email_on_activity,
            "digest_frequency": self.digest_frequency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
