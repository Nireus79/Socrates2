"""
Invoice model for billing records.

Tracks all invoices from Stripe.
"""

from sqlalchemy import JSONB, Column, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class Invoice(BaseModel):
    """Billing invoice from Stripe."""
    __tablename__ = "invoices"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(PG_UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True)
    stripe_invoice_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='usd', nullable=False)
    status = Column(String(20), nullable=False)  # draft, open, paid, uncollectible, void
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    hosted_invoice_url = Column(String(500), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Timestamps
    invoice_date = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_invoice_user", "user_id"),
        Index("idx_invoice_status", "status"),
        Index("idx_invoice_stripe_id", "stripe_invoice_id"),
        Index("idx_invoice_date", "invoice_date"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "stripe_invoice_id": self.stripe_invoice_id,
            "amount_paid": float(self.amount_paid),
            "amount_due": float(self.amount_due),
            "currency": self.currency,
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "hosted_invoice_url": self.hosted_invoice_url,
            "pdf_url": self.pdf_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
