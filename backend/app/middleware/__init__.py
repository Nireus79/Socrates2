"""
Middleware for Socrates API.

Provides cross-cutting concerns like rate limiting, logging, and authentication.
"""

from .rate_limit_middleware import RateLimitMiddleware

__all__ = ["RateLimitMiddleware"]
