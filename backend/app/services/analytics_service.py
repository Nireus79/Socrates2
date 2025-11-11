"""
Analytics aggregation service.

Calculates and stores business metrics:
- Daily Active Users (DAU)
- Monthly Recurring Revenue (MRR)
- Churn analysis
- Feature usage
- Conversion funnel
"""
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ..models.analytics_metrics import (
    ChurnAnalysis,
    ConversionFunnel,
    DailyActiveUsers,
    MonthlyRecurringRevenue,
)
from ..models.session import Session as UserSession
from ..models.subscription import Subscription
from ..models.user import User

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Calculate and aggregate business metrics."""

    @staticmethod
    def calculate_daily_active_users(date_to_calc: date, db_auth: Session, db_specs: Session) -> DailyActiveUsers:
        """
        Calculate daily active users for a specific date.

        Args:
            date_to_calc: Date to calculate for
            db_auth: Auth database session
            db_specs: Specs database session

        Returns:
            DailyActiveUsers metric
        """
        start = datetime.combine(date_to_calc, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        # Count sessions
        total_sessions = db_specs.query(UserSession).filter(
            and_(
                UserSession.created_at >= start,
                UserSession.created_at < end
            )
        ).count()

        # Count unique users
        unique_users = db_specs.query(func.count(func.distinct(UserSession.user_id))).filter(
            and_(
                UserSession.created_at >= start,
                UserSession.created_at < end
            )
        ).scalar() or 0

        # Count new users (created today)
        new_users = db_auth.query(User).filter(
            and_(
                User.created_at >= start,
                User.created_at < end
            )
        ).count()

        returning_users = unique_users - new_users

        # Check if metric already exists
        existing = db_specs.query(DailyActiveUsers).filter(DailyActiveUsers.date == date_to_calc).first()

        if existing:
            existing.count = unique_users
            existing.new_users = new_users
            existing.returning_users = returning_users
            db_specs.add(existing)
        else:
            metric = DailyActiveUsers(
                date=date_to_calc,
                count=unique_users,
                new_users=new_users,
                returning_users=returning_users,
            )
            db_specs.add(metric)

        db_specs.commit()
        logger.info(f"Calculated DAU for {date_to_calc}: {unique_users} users")

        return existing or metric

    @staticmethod
    def calculate_monthly_recurring_revenue(month_start: date, db_auth: Session, db_specs: Session) -> MonthlyRecurringRevenue:
        """
        Calculate monthly recurring revenue.

        Args:
            month_start: First day of month
            db_auth: Auth database session
            db_specs: Specs database session

        Returns:
            MonthlyRecurringRevenue metric
        """
        # Get all active subscriptions on this date
        subscriptions = db_specs.query(Subscription).filter(
            and_(
                Subscription.created_at <= datetime.combine(month_start, datetime.max.time(), tzinfo=timezone.utc),
                or_(
                    Subscription.canceled_at.is_(None),
                    Subscription.canceled_at >= month_start
                )
            )
        ).all()

        # Calculate MRR from subscription prices
        # This is simplified - in production, fetch from Stripe price data
        total_mrr = Decimal(0)
        by_tier = {}

        for sub in subscriptions:
            # Pricing by tier
            tier_prices = {
                "pro": Decimal("29.00"),
                "team": Decimal("99.00"),
                "enterprise": Decimal("0.00"),  # Custom pricing
            }
            price = tier_prices.get(sub.tier, Decimal(0))
            total_mrr += price

            if sub.tier not in by_tier:
                by_tier[sub.tier] = {"count": 0, "mrr": 0}
            by_tier[sub.tier]["count"] += 1
            by_tier[sub.tier]["mrr"] = float(by_tier[sub.tier]["mrr"]) + float(price)

        # Check if metric already exists
        existing = db_specs.query(MonthlyRecurringRevenue).filter(
            MonthlyRecurringRevenue.month_start == month_start
        ).first()

        if existing:
            existing.total_mrr = total_mrr
            existing.by_tier = by_tier
            db_specs.add(existing)
        else:
            metric = MonthlyRecurringRevenue(
                month_start=month_start,
                total_mrr=total_mrr,
                by_tier=by_tier,
            )
            db_specs.add(metric)

        db_specs.commit()
        logger.info(f"Calculated MRR for {month_start}: ${float(total_mrr)}")

        return existing or metric

    @staticmethod
    def calculate_churn(date_to_calc: date, db_specs: Session) -> ChurnAnalysis:
        """
        Calculate user churn for a date.

        Args:
            date_to_calc: Date to calculate for
            db_specs: Specs database session

        Returns:
            ChurnAnalysis metric
        """
        start = datetime.combine(date_to_calc, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        # Count canceled subscriptions today
        churned = db_specs.query(Subscription).filter(
            and_(
                Subscription.canceled_at >= start,
                Subscription.canceled_at < end
            )
        ).all()

        churned_count = len(churned)

        # Count active subscriptions at start of day for churn rate
        active_subs = db_specs.query(Subscription).filter(
            and_(
                Subscription.created_at <= start,
                or_(
                    Subscription.canceled_at.is_(None),
                    Subscription.canceled_at >= start
                )
            )
        ).count()

        churn_rate = (Decimal(churned_count) / Decimal(active_subs) * 100) if active_subs > 0 else Decimal(0)

        # By tier breakdown
        by_tier = {}
        for sub in churned:
            if sub.tier not in by_tier:
                by_tier[sub.tier] = {"count": 0, "rate": 0}
            by_tier[sub.tier]["count"] += 1

        # Check if metric already exists
        existing = db_specs.query(ChurnAnalysis).filter(ChurnAnalysis.date == date_to_calc).first()

        if existing:
            existing.churned_users = churned_count
            existing.churn_rate_percent = churn_rate
            existing.by_tier = by_tier
            db_specs.add(existing)
        else:
            metric = ChurnAnalysis(
                date=date_to_calc,
                churned_users=churned_count,
                churn_rate_percent=churn_rate,
                by_tier=by_tier,
            )
            db_specs.add(metric)

        db_specs.commit()
        logger.info(f"Calculated churn for {date_to_calc}: {churned_count} users ({float(churn_rate):.2f}%)")

        return existing or metric

    @staticmethod
    def calculate_conversion_funnel(date_to_calc: date, db_auth: Session, db_specs: Session) -> ConversionFunnel:
        """
        Calculate signup to paid conversion funnel.

        Args:
            date_to_calc: Date to calculate for
            db_auth: Auth database session
            db_specs: Specs database session

        Returns:
            ConversionFunnel metric
        """
        start = datetime.combine(date_to_calc, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        # Signups
        signups = db_auth.query(User).filter(
            and_(
                User.created_at >= start,
                User.created_at < end
            )
        ).count()

        # Trial started (users with trial_ends_at set)
        trial_started = db_auth.query(User).filter(
            and_(
                User.created_at >= start,
                User.created_at < end,
                User.trial_ends_at.isnot(None)
            )
        ).count()

        # Paid users (subscription created)
        paid_users = db_specs.query(Subscription).filter(
            and_(
                Subscription.created_at >= start,
                Subscription.created_at < end,
                Subscription.status.in_(["active", "past_due"])
            )
        ).count()

        # Trial to paid
        trial_to_paid = paid_users  # Simplified

        # Conversion rate
        conversion_rate = (Decimal(paid_users) / Decimal(signups) * 100) if signups > 0 else Decimal(0)

        # Check if metric already exists
        existing = db_specs.query(ConversionFunnel).filter(ConversionFunnel.date == date_to_calc).first()

        if existing:
            existing.signups = signups
            existing.trial_started = trial_started
            existing.trial_to_paid = trial_to_paid
            existing.paid_users = paid_users
            existing.conversion_rate_percent = conversion_rate
            db_specs.add(existing)
        else:
            metric = ConversionFunnel(
                date=date_to_calc,
                signups=signups,
                trial_started=trial_started,
                trial_to_paid=trial_to_paid,
                paid_users=paid_users,
                conversion_rate_percent=conversion_rate,
            )
            db_specs.add(metric)

        db_specs.commit()
        logger.info(f"Calculated funnel for {date_to_calc}: {signups} → {trial_started} → {paid_users}")

        return existing or metric

    @staticmethod
    def get_current_metrics(db_auth: Session, db_specs: Session) -> dict:
        """
        Get latest metrics snapshot.

        Args:
            db_auth: Auth database session
            db_specs: Specs database session

        Returns:
            Dictionary with current metrics
        """
        yesterday = date.today() - timedelta(days=1)
        month_start = date.today().replace(day=1)

        dau = db_specs.query(DailyActiveUsers).filter(
            DailyActiveUsers.date == yesterday
        ).first()

        mrr = db_specs.query(MonthlyRecurringRevenue).filter(
            MonthlyRecurringRevenue.month_start == month_start
        ).first()

        churn = db_specs.query(ChurnAnalysis).filter(
            ChurnAnalysis.date == yesterday
        ).first()

        funnel = db_specs.query(ConversionFunnel).filter(
            ConversionFunnel.date == yesterday
        ).first()

        return {
            "dau": dau.to_dict() if dau else None,
            "mrr": mrr.to_dict() if mrr else None,
            "churn": churn.to_dict() if churn else None,
            "funnel": funnel.to_dict() if funnel else None,
        }
