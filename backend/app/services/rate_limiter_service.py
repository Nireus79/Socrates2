"""
Rate limiting service for API endpoints.

Provides:
- Per-user rate limiting
- Per-IP rate limiting
- Sliding window with TTL
- Configurable limits and windows
"""
import logging
import time
from functools import wraps
from typing import Callable, Dict, Optional, Tuple

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple sliding window rate limiter."""

    def __init__(self):
        """Initialize rate limiter with empty tracking dict."""
        self._requests = {}

    def _cleanup_expired(self, key: str, window_seconds: int):
        """Remove expired entries for a key."""
        if key not in self._requests:
            return

        current_time = time.time()
        cutoff = current_time - window_seconds

        # Keep only recent requests
        self._requests[key] = [
            req_time for req_time in self._requests[key]
            if req_time > cutoff
        ]

        # Remove key if no requests left
        if not self._requests[key]:
            del self._requests[key]

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Identifier (user_id, IP, etc)
            max_requests: Max requests in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed: bool, info: dict with remaining, reset_after)
        """
        current_time = time.time()

        # Clean up expired entries
        self._cleanup_expired(key, window_seconds)

        # Get current request count
        if key not in self._requests:
            self._requests[key] = []

        current_count = len(self._requests[key])

        # Calculate info
        window_end = self._requests[key][0] + window_seconds if self._requests[key] else current_time + window_seconds
        reset_after = max(0, int(window_end - current_time))
        remaining = max(0, max_requests - current_count)

        info = {
            "limit": max_requests,
            "remaining": remaining,
            "reset_after": reset_after,
            "window_seconds": window_seconds
        }

        if current_count >= max_requests:
            return False, info

        # Record this request
        self._requests[key].append(current_time)

        return True, info


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for rate limiting endpoints.

    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        key_builder: Function to build rate limit key from request/args
                    Default: uses remote IP address

    Example:
        @app.get("/api/data")
        @rate_limit(max_requests=10, window_seconds=60)
        def get_data(request: Request):
            return {"data": "value"}

        # Per-user rate limiting
        @app.get("/api/user-data")
        @rate_limit(
            max_requests=100,
            window_seconds=3600,
            key_builder=lambda req, user_id: f"user:{user_id}"
        )
        def get_user_data(request: Request, user_id: str):
            return {"data": "value"}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Find request object in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and "request" in kwargs:
                request = kwargs["request"]

            if not request:
                logger.warning(f"Could not find Request object in {func.__name__}")
                return await func(*args, **kwargs)

            # Build rate limit key
            if key_builder:
                rate_limit_key = key_builder(request, *args, **kwargs)
            else:
                # Default: use client IP
                client_ip = request.client.host if request.client else "unknown"
                rate_limit_key = f"ip:{client_ip}:{func.__name__}"

            # Check rate limit
            allowed, info = _rate_limiter.is_allowed(
                rate_limit_key,
                max_requests,
                window_seconds
            )

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {rate_limit_key}: "
                    f"{max_requests} requests per {window_seconds}s"
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "reset_after": info["reset_after"],
                        "limit": info["limit"]
                    }
                )

            # Add rate limit info to response headers (via request.state)
            if hasattr(request, "state"):
                request.state.rate_limit_limit = info["limit"]
                request.state.rate_limit_remaining = info["remaining"]
                request.state.rate_limit_reset = info["reset_after"]

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Find request object in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and "request" in kwargs:
                request = kwargs["request"]

            if not request:
                logger.warning(f"Could not find Request object in {func.__name__}")
                return func(*args, **kwargs)

            # Build rate limit key
            if key_builder:
                rate_limit_key = key_builder(request, *args, **kwargs)
            else:
                # Default: use client IP
                client_ip = request.client.host if request.client else "unknown"
                rate_limit_key = f"ip:{client_ip}:{func.__name__}"

            # Check rate limit
            allowed, info = _rate_limiter.is_allowed(
                rate_limit_key,
                max_requests,
                window_seconds
            )

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {rate_limit_key}: "
                    f"{max_requests} requests per {window_seconds}s"
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "reset_after": info["reset_after"],
                        "limit": info["limit"]
                    }
                )

            # Add rate limit info to response headers (via request.state)
            if hasattr(request, "state"):
                request.state.rate_limit_limit = info["limit"]
                request.state.rate_limit_remaining = info["remaining"]
                request.state.rate_limit_reset = info["reset_after"]

            return func(*args, **kwargs)

        # Determine if function is async or sync
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def rate_limit_user(
    max_requests: int = 100,
    window_seconds: int = 60
):
    """
    Decorator for per-user rate limiting.

    Automatically extracts user_id from request context.

    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds

    Example:
        @app.get("/api/user-data")
        @rate_limit_user(max_requests=100, window_seconds=3600)
        def get_user_data(current_user: User = Depends(get_current_active_user)):
            return {"data": "value"}
    """
    def key_builder(request: Request, *args, **kwargs):
        # Try to get user_id from kwargs (if passed as current_user)
        for arg in args:
            if hasattr(arg, 'id'):  # Assume it's a User object
                return f"user:{arg.id}"

        # Fallback to IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    return rate_limit(max_requests, window_seconds, key_builder)


def get_rate_limit_headers(request: Request) -> Dict[str, str]:
    """
    Extract rate limit headers from request state.

    Should be used in response to add rate limit info to HTTP headers.

    Args:
        request: FastAPI Request object

    Returns:
        Dict with rate limit headers (empty if no rate limit info)
    """
    headers = {}

    if hasattr(request, "state"):
        if hasattr(request.state, "rate_limit_limit"):
            headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
        if hasattr(request.state, "rate_limit_remaining"):
            headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
        if hasattr(request.state, "rate_limit_reset"):
            headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)

    return headers
