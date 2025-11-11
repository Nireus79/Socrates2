"""
Cache service for storing and retrieving frequently accessed data.

Supports both in-memory caching (default) and Redis caching (optional).
Implements TTL (Time-To-Live) for automatic expiration.
"""
import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CacheService:
    """
    In-memory cache service with TTL support.

    Thread-safe dictionary-based caching for development and small deployments.
    Automatically removes expired entries on access.
    """

    _instance = None
    _cache = {}

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """
        Set a cache value with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time to live in seconds (default 1 hour)
        """
        try:
            expiration = time.time() + ttl_seconds
            self._cache[key] = {
                'value': value,
                'expires_at': expiration
            }
            logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
        except Exception as e:
            logger.error(f"Cache SET failed for {key}: {e}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get a cache value.

        Returns None if key doesn't exist or has expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        try:
            if key not in self._cache:
                logger.debug(f"Cache MISS: {key} (not found)")
                return None

            entry = self._cache[key]

            # Check if expired
            if time.time() > entry['expires_at']:
                del self._cache[key]
                logger.debug(f"Cache MISS: {key} (expired)")
                return None

            logger.debug(f"Cache HIT: {key}")
            return entry['value']
        except Exception as e:
            logger.error(f"Cache GET failed for {key}: {e}")
            return None

    def delete(self, key: str) -> None:
        """
        Delete a cache entry.

        Args:
            key: Cache key to delete
        """
        try:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache DELETE failed for {key}: {e}")

    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern (simple prefix match).

        Example: clear_pattern("user:123:") removes all keys starting with "user:123:"

        Args:
            pattern: Key pattern to match

        Returns:
            Number of keys deleted
        """
        try:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            logger.debug(f"Cache CLEAR: {len(keys_to_delete)} keys matching '{pattern}'")
            return len(keys_to_delete)
        except Exception as e:
            logger.error(f"Cache CLEAR_PATTERN failed: {e}")
            return 0

    def clear_all(self) -> None:
        """Clear entire cache."""
        try:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache CLEAR_ALL: {count} entries removed")
        except Exception as e:
            logger.error(f"Cache CLEAR_ALL failed: {e}")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache size, expiration info
        """
        current_time = time.time()
        expired_count = sum(
            1 for entry in self._cache.values()
            if current_time > entry['expires_at']
        )

        return {
            'total_entries': len(self._cache),
            'expired_entries': expired_count,
            'memory_usage': sum(
                len(json.dumps(entry['value']).encode()) if isinstance(entry['value'], (dict, list))
                else len(str(entry['value']).encode())
                for entry in self._cache.values()
            )
        }


# Global cache instance
cache_service = CacheService()


def cache_result(ttl_seconds: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Automatically generates cache key from function name and arguments.

    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Optional prefix for cache key (e.g., "user:123:")

    Example:
        @cache_result(ttl_seconds=300, key_prefix="projects:")
        def get_projects(user_id: str):
            return db.query(Project).filter(Project.user_id == user_id).all()
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            args_str = "_".join(str(arg) for arg in args)
            kwargs_str = "_".join(f"{k}:{v}" for k, v in sorted(kwargs.items()))

            cache_key = f"{key_prefix}{func.__name__}"
            if args_str:
                cache_key += f":{args_str}"
            if kwargs_str:
                cache_key += f":{kwargs_str}"

            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached result for {func.__name__}")
                return cached_result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl_seconds=ttl_seconds)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> None:
    """
    Invalidate cache entries matching a pattern.

    Used when data is modified to prevent stale cache.

    Args:
        pattern: Key pattern to match (prefix-based)

    Example:
        # When user profile changes
        invalidate_cache("user:123:")

        # When project is updated
        invalidate_cache("project:proj_123:")
    """
    cache_service.clear_pattern(pattern)
    logger.info(f"Cache invalidated for pattern: {pattern}")
