"""
Analytics metrics models for dashboard.

Tracks business metrics: DAU, MRR, churn, funnel, etc.
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Date, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from datetime import datetime, timezone, date

from .base import BaseModel


class DailyActiveUsers(BaseModel):
    """Daily active users metric."""

    __tablename__ = "daily_active_users"

    date = Column(Date, nullable=False, unique=True, index=True)
    count = Column(Integer, nullable=False, default=0)
    new_users = Column(Integer, nullable=False, default=0)
    returning_users = Column(Integer, nullable=False, default=0)
    breakdown = Column(JSONB, nullable=True)  # By tier, region, etc.

    __table_args__ = (
        Index("idx_dau_date", "date"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "date": self.date.isoformat(),
            "count": self.count,
            "new_users": self.new_users,
            "returning_users": self.returning_users,
            "breakdown": self.breakdown or {},
        }


class MonthlyRecurringRevenue(BaseModel):
    """Monthly recurring revenue metric."""

    __tablename__ = "monthly_recurring_revenue"

    month_start = Column(Date, nullable=False, unique=True, index=True)
    total_mrr = Column(Numeric(12, 2), nullable=False, default=0)
    new_mrr = Column(Numeric(12, 2), nullable=False, default=0)
    churned_mrr = Column(Numeric(12, 2), nullable=False, default=0)
    by_tier = Column(JSONB, nullable=True)  # MRR breakdown by subscription tier

    __table_args__ = (
        Index("idx_mrr_month", "month_start"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "month_start": self.month_start.isoformat(),
            "total_mrr": float(self.total_mrr or 0),
            "new_mrr": float(self.new_mrr or 0),
            "churned_mrr": float(self.churned_mrr or 0),
            "by_tier": self.by_tier or {},
        }


class ChurnAnalysis(BaseModel):
    """User churn analysis."""

    __tablename__ = "churn_analysis"

    date = Column(Date, nullable=False, unique=True, index=True)
    churned_users = Column(Integer, nullable=False, default=0)
    churn_rate_percent = Column(Numeric(5, 2), nullable=False, default=0)
    by_tier = Column(JSONB, nullable=True)  # Churn rate by tier
    by_region = Column(JSONB, nullable=True)  # Churn rate by region
    reasons = Column(JSONB, nullable=True)  # Top churn reasons

    __table_args__ = (
        Index("idx_churn_date", "date"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "date": self.date.isoformat(),
            "churned_users": self.churned_users,
            "churn_rate_percent": float(self.churn_rate_percent or 0),
            "by_tier": self.by_tier or {},
            "by_region": self.by_region or {},
            "reasons": self.reasons or [],
        }


class FeatureUsage(BaseModel):
    """Feature adoption and usage tracking."""

    __tablename__ = "feature_usage"

    date = Column(Date, nullable=False, index=True)
    feature_name = Column(String(100), nullable=False, index=True)
    users_using = Column(Integer, nullable=False, default=0)
    total_uses = Column(Integer, nullable=False, default=0)
    avg_uses_per_user = Column(Numeric(6, 2), nullable=False, default=0)

    __table_args__ = (
        Index("idx_feature_date", "date"),
        Index("idx_feature_name", "feature_name"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "date": self.date.isoformat(),
            "feature_name": self.feature_name,
            "users_using": self.users_using,
            "total_uses": self.total_uses,
            "avg_uses_per_user": float(self.avg_uses_per_user or 0),
        }


class ConversionFunnel(BaseModel):
    """Signup to paid conversion funnel."""

    __tablename__ = "conversion_funnel"

    date = Column(Date, nullable=False, unique=True, index=True)
    signups = Column(Integer, nullable=False, default=0)
    trial_started = Column(Integer, nullable=False, default=0)
    trial_to_paid = Column(Integer, nullable=False, default=0)
    paid_users = Column(Integer, nullable=False, default=0)
    conversion_rate_percent = Column(Numeric(5, 2), nullable=False, default=0)

    __table_args__ = (
        Index("idx_funnel_date", "date"),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "date": self.date.isoformat(),
            "signups": self.signups,
            "trial_started": self.trial_started,
            "trial_to_paid": self.trial_to_paid,
            "paid_users": self.paid_users,
            "conversion_rate_percent": float(self.conversion_rate_percent or 0),
        }
