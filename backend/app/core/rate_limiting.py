"""
Rate limiting middleware.

Tracks and enforces API rate limits per user.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter for API requests."""

    def __init__(self):
        """Initialize rate limiter."""
        # Store request counts per user per day
        # Format: {user_id: {date: count, timestamp: datetime}}
        self.requests: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "reset_at": None})

    def is_allowed(self, user_id: str, limit: Optional[int]) -> bool:
        """
        Check if user is within rate limit.

        Args:
            user_id: User ID
            limit: Requests per day limit (None = unlimited)

        Returns:
            True if request is allowed, False if limit exceeded
        """
        if limit is None:
            return True  # Unlimited

        now = datetime.now(timezone.utc)
        user_data = self.requests[user_id]

        # Reset counter if it's a new day
        if user_data["reset_at"] is None or now > user_data["reset_at"]:
            user_data["count"] = 0
            user_data["reset_at"] = now + timedelta(days=1)

        # Check limit
        if user_data["count"] >= limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False

        # Increment counter
        user_data["count"] += 1
        return True

    def get_remaining(self, user_id: str, limit: Optional[int]) -> Optional[int]:
        """
        Get remaining requests for user today.

        Args:
            user_id: User ID
            limit: Requests per day limit (None = unlimited)

        Returns:
            Remaining requests, or None if unlimited
        """
        if limit is None:
            return None

        user_data = self.requests[user_id]
        return max(0, limit - user_data["count"])

    def reset_user(self, user_id: str) -> None:
        """Reset user's rate limit counter."""
        if user_id in self.requests:
            self.requests[user_id] = {"count": 0, "reset_at": None}


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset global rate limiter (for testing)."""
    global _rate_limiter
    _rate_limiter = None
