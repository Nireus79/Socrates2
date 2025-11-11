"""
Usage limiting and quota enforcement.

Enforces subscription tier limits:
- Project creation limits
- Team member limits
- API rate limiting
- Storage limits
"""
import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ..core.subscription_tiers import (
    SubscriptionTier,
    can_add_team_member,
    can_create_project,
    get_api_rate_limit,
)
from ..models.user import User

logger = logging.getLogger(__name__)


class UsageLimitError(Exception):
    """Raised when user exceeds usage limits."""

    def __init__(self, limit_type: str, message: str, limit: Optional[int] = None):
        self.limit_type = limit_type
        self.message = message
        self.limit = limit
        super().__init__(message)


class UsageLimiter:
    """Check and enforce usage limits for users."""

    @staticmethod
    def check_project_creation(
        user: User,
        db: Session,
        tier: Optional[SubscriptionTier] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can create a new project.

        Args:
            user: User object
            db: Database session
            tier: Optional tier override

        Returns:
            Tuple of (can_create, error_message)
        """
        tier = tier or SubscriptionTier(user.subscription_tier or "free")

        # Get current project count
        from ..models.project import Project
        current_count = db.query(Project).filter(
            Project.user_id == user.id
        ).count()

        # Check limit
        if not can_create_project(tier, current_count):
            limit = 3 if tier == SubscriptionTier.FREE else (
                25 if tier == SubscriptionTier.PRO else None
            )
            raise UsageLimitError(
                "project_limit",
                f"Project limit of {limit} reached for {tier.value} tier",
                limit
            )

        return True, None

    @staticmethod
    def check_team_member_addition(
        user: User,
        db: Session,
        tier: Optional[SubscriptionTier] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can add a new team member.

        Args:
            user: User object
            db: Database session
            tier: Optional tier override

        Returns:
            Tuple of (can_add, error_message)
        """
        tier = tier or SubscriptionTier(user.subscription_tier or "free")

        # Get current team member count
        from ..models.team_member import TeamMember
        current_count = db.query(TeamMember).filter(
            TeamMember.team_id == user.id  # Assuming user.id is team_id
        ).count()

        # Check limit
        if not can_add_team_member(tier, current_count):
            limit = 1 if tier == SubscriptionTier.FREE else (
                5 if tier == SubscriptionTier.PRO else (
                    50 if tier == SubscriptionTier.TEAM else None
                )
            )
            raise UsageLimitError(
                "team_member_limit",
                f"Team member limit of {limit} reached for {tier.value} tier",
                limit
            )

        return True, None

    @staticmethod
    def get_api_rate_limit(user: User) -> Optional[int]:
        """
        Get API rate limit for user per day.

        Args:
            user: User object

        Returns:
            Requests per day limit, or None if unlimited
        """
        tier = SubscriptionTier(user.subscription_tier or "free")
        return get_api_rate_limit(tier)

    @staticmethod
    def check_api_quota(
        user: User,
        db: Session,
        requests_today: int = 0
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if user is within API quota.

        Args:
            user: User object
            db: Database session
            requests_today: Number of requests made today

        Returns:
            Tuple of (within_quota, requests_remaining)
        """
        limit = UsageLimiter.get_api_rate_limit(user)

        if limit is None:
            return True, None  # Unlimited

        remaining = limit - requests_today

        if remaining <= 0:
            raise UsageLimitError(
                "api_quota_exceeded",
                f"Daily API quota of {limit} requests exceeded",
                limit
            )

        return True, remaining

    @staticmethod
    def get_storage_limit_gb(user: User) -> Optional[float]:
        """
        Get storage limit for user in GB.

        Args:
            user: User object

        Returns:
            Storage limit in GB, or None if unlimited
        """
        tier = SubscriptionTier(user.subscription_tier or "free")
        from ..core.subscription_tiers import get_tier_limit
        return get_tier_limit(tier, "storage_gb")

    @staticmethod
    def check_storage_limit(
        user: User,
        db: Session,
        additional_size_bytes: int = 0
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if user can store more data.

        Args:
            user: User object
            db: Database session
            additional_size_bytes: Size of data to be added

        Returns:
            Tuple of (within_limit, storage_remaining_gb)
        """
        limit_gb = UsageLimiter.get_storage_limit_gb(user)

        if limit_gb is None:
            return True, None  # Unlimited

        # Get current storage usage
        # TODO: Implement storage calculation
        current_usage_gb = 0.0

        available_gb = limit_gb - current_usage_gb
        additional_size_gb = additional_size_bytes / (1024 ** 3)

        if additional_size_gb > available_gb:
            raise UsageLimitError(
                "storage_limit_exceeded",
                f"Storage limit of {limit_gb}GB exceeded. Available: {available_gb}GB",
                int(limit_gb)
            )

        return True, available_gb - additional_size_gb

    @staticmethod
    def get_tier_limits_summary(user: User) -> dict:
        """
        Get a summary of all limits for user's tier.

        Args:
            user: User object

        Returns:
            Dictionary with all tier limits
        """
        tier = SubscriptionTier(user.subscription_tier or "free")
        from ..core.subscription_tiers import get_tier_info

        tier_info = get_tier_info(tier) or {}

        return {
            "tier": tier.value,
            "max_projects": tier_info.get("max_projects"),
            "max_specifications": tier_info.get("max_specifications"),
            "max_team_members": tier_info.get("max_team_members"),
            "api_requests_per_day": tier_info.get("api_requests_per_day"),
            "storage_gb": tier_info.get("storage_gb"),
            "features": tier_info.get("features", []),
        }
