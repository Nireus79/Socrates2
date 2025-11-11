"""
Subscription model for Stripe billing integration.

Tracks active subscriptions and their status.
"""

from sqlalchemy import JSONB, Boolean, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class Subscription(BaseModel):
    """Stripe subscription record."""
    __tablename__ = "subscriptions"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=False)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # active, canceled, past_due, paused
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    tier = Column(String(20), nullable=False)  # pro, team, enterprise
    billing_cycle_anchor = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, nullable=True)  # Store custom metadata
    price_id = Column(String(255), nullable=True)  # Stripe price ID

    # Timestamps
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_subscription_user", "user_id"),
        Index("idx_subscription_status", "status"),
        Index("idx_subscription_stripe_id", "stripe_subscription_id"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "stripe_subscription_id": self.stripe_subscription_id,
            "stripe_customer_id": self.stripe_customer_id,
            "status": self.status,
            "tier": self.tier,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "cancel_at_period_end": self.cancel_at_period_end,
            "canceled_at": self.canceled_at.isoformat() if self.canceled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
