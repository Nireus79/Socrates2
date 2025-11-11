"""
Trial management service.

Handles free trial logic:
- Trial creation
- Expiration detection
- Grace period handling
- Trial warnings
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from ..models.user import User

logger = logging.getLogger(__name__)

# Trial configuration
FREE_TRIAL_DAYS = 14
GRACE_PERIOD_DAYS = 3
WARNING_DAYS = [7, 3, 1]


class TrialService:
    """Manage free trial logic."""

    @staticmethod
    def start_trial(user: User) -> None:
        """
        Start a free trial for a user.

        Args:
            user: User object to initialize trial for
        """
        user.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=FREE_TRIAL_DAYS)
        user.subscription_tier = "free"
        user.subscription_status = "active"
        logger.info(f"Started trial for user {user.id}, expires at {user.trial_ends_at}")

    @staticmethod
    def is_trial_expired(user: User) -> bool:
        """
        Check if trial has expired.

        Args:
            user: User object

        Returns:
            True if trial has passed expiration date, False otherwise
        """
        if not user.trial_ends_at:
            return False
        return datetime.now(timezone.utc) > user.trial_ends_at

    @staticmethod
    def is_in_grace_period(user: User) -> bool:
        """
        Check if user is in 3-day grace period after trial expiration.

        Args:
            user: User object

        Returns:
            True if in grace period, False otherwise
        """
        if not user.trial_ends_at:
            return False

        now = datetime.now(timezone.utc)
        days_since_expiry = (now - user.trial_ends_at).days

        return 0 < days_since_expiry <= GRACE_PERIOD_DAYS

    @staticmethod
    def days_until_trial_expiry(user: User) -> int:
        """
        Get number of days remaining in trial.

        Args:
            user: User object

        Returns:
            Days remaining (0 if expired or no trial)
        """
        if not user.trial_ends_at:
            return 0

        delta = user.trial_ends_at - datetime.now(timezone.utc)
        return max(0, delta.days)

    @staticmethod
    def should_send_warning(user: User) -> bool:
        """
        Check if a trial expiration warning should be sent.

        Args:
            user: User object

        Returns:
            True if warning should be sent, False otherwise
        """
        if not user.trial_ends_at:
            return False

        days_remaining = TrialService.days_until_trial_expiry(user)
        return days_remaining in WARNING_DAYS

    @staticmethod
    def get_trial_status(user: User) -> Dict[str, Any]:
        """
        Get comprehensive trial status for a user.

        Args:
            user: User object

        Returns:
            Dictionary with trial status information
        """
        return {
            "has_trial": user.trial_ends_at is not None,
            "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
            "is_expired": TrialService.is_trial_expired(user),
            "is_in_grace_period": TrialService.is_in_grace_period(user),
            "days_remaining": TrialService.days_until_trial_expiry(user),
            "should_warn": TrialService.should_send_warning(user),
            "grace_period_days": GRACE_PERIOD_DAYS if TrialService.is_in_grace_period(user) else 0,
        }

    @staticmethod
    def can_access(user: User) -> bool:
        """
        Check if user can access the system.

        Users can access if:
        - Trial is active
        - Trial expired but in grace period
        - Paid subscription active
        - User is admin

        Args:
            user: User object

        Returns:
            True if user can access, False otherwise
        """
        # Admins always have access
        if user.role == "admin":
            return True

        # Paid users have access
        if user.subscription_tier != "free":
            return True

        # Trial users have access if trial active or in grace period
        if user.trial_ends_at:
            if not TrialService.is_trial_expired(user):
                return True  # Trial active

            if TrialService.is_in_grace_period(user):
                return True  # Grace period

        # No trial and not paid
        return False

    @staticmethod
    def upgrade_from_trial(user: User, tier: str) -> None:
        """
        Convert user from trial to paid subscription.

        Args:
            user: User object
            tier: Subscription tier (pro, team, enterprise)
        """
        user.subscription_tier = tier
        user.subscription_status = "active"
        user.trial_ends_at = None  # Clear trial end date
        logger.info(f"Upgraded user {user.id} from trial to {tier}")

    @staticmethod
    def downgrade_to_free(user: User) -> None:
        """
        Downgrade a paid user back to free.

        Args:
            user: User object
        """
        user.subscription_tier = "free"
        user.subscription_status = "active"
        user.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=FREE_TRIAL_DAYS)
        logger.info(f"Downgraded user {user.id} to free, new trial: {user.trial_ends_at}")
