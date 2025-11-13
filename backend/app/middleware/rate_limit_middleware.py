"""
Rate limiting middleware for FastAPI.

Enforces API rate limits on incoming requests based on user subscription tier.
"""
import logging
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.rate_limiting import get_rate_limiter
from ..core.subscription_tiers import TIER_LIMITS, SubscriptionTier

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces rate limits on API requests.

    Checks the user's subscription tier and enforces the corresponding
    API request limit. Returns 429 (Too Many Requests) when limit exceeded.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> any:
        """
        Process request and check rate limits.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint

        Returns:
            Response or 429 if rate limit exceeded
        """
        # Skip rate limiting for certain endpoints
        skip_paths = ["/", "/docs", "/openapi.json", "/api/v1/info", "/api/v1/admin/health"]
        if request.url.path in skip_paths or request.url.path.startswith("/api/v1/auth/"):
            return await call_next(request)

        # Try to get user ID from request
        user_id = self._get_user_id(request)
        if not user_id:
            # No user, skip rate limiting (likely unauthenticated endpoint)
            return await call_next(request)

        # Try to get user's subscription tier
        user_tier = self._get_user_tier(request)
        if not user_tier:
            user_tier = SubscriptionTier.FREE

        # Get tier's API rate limit
        tier_limits = TIER_LIMITS.get(user_tier, {})
        daily_limit = tier_limits.get("api_requests_per_day")

        if daily_limit is None:
            # Unlimited tier, allow request
            response = await call_next(request)
            return response

        # Check rate limit
        limiter = get_rate_limiter()
        is_allowed = limiter.is_allowed(user_id, daily_limit)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_id} (tier: {user_tier.name})")

            remaining = limiter.get_remaining(user_id, daily_limit)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Limit: {daily_limit} requests per day",
                    "limit": daily_limit,
                    "remaining": remaining or 0,
                },
            )

        # Request allowed, proceed
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = limiter.get_remaining(user_id, daily_limit)
        response.headers["X-RateLimit-Limit"] = str(daily_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining or 0)
        response.headers["X-RateLimit-Tier"] = user_tier.name

        return response

    @staticmethod
    def _get_user_id(request: Request) -> str:
        """
        Extract user ID from request.

        Looks for user ID in:
        1. JWT token (sub claim)
        2. query parameter (user_id)

        Args:
            request: HTTP request

        Returns:
            User ID if found, None otherwise
        """
        # Try to get from authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from ..core.security import decode_access_token

                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                user_id = payload.get("sub")
                if user_id:
                    return user_id
            except Exception:
                pass

        # Try to get from query parameter (for WebSocket or other cases)
        user_id = request.query_params.get("user_id")
        if user_id:
            return user_id

        return None

    @staticmethod
    def _get_user_tier(request: Request) -> SubscriptionTier:
        """
        Extract user subscription tier from request.

        Looks for tier in:
        1. JWT token (tier claim)
        2. Custom header (X-Subscription-Tier)

        Args:
            request: HTTP request

        Returns:
            SubscriptionTier if found, None otherwise
        """
        # Try to get from authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from ..core.security import decode_access_token

                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                tier_str = payload.get("tier")
                if tier_str:
                    return SubscriptionTier[tier_str]
            except Exception:
                pass

        # Try to get from custom header
        tier_header = request.headers.get("X-Subscription-Tier")
        if tier_header:
            try:
                return SubscriptionTier[tier_header]
            except KeyError:
                pass

        return None
