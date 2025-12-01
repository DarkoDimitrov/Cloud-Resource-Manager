import redis
import json
from typing import Any, Optional
from ..config import get_settings

settings = get_settings()


class CacheManager:
    """Redis cache manager for storing frequently accessed data."""

    def __init__(self):
        """Initialize cache manager."""
        self._redis_client = None

    def _get_client(self):
        """Get or create Redis client."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True
                )
            except Exception as e:
                print(f"Failed to connect to Redis: {e}")
                self._redis_client = None
        return self._redis_client

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            if not settings.cache_enabled:
                return None

            client = self._get_client()
            if client is None:
                return None

            value = client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get failed for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)

        Returns:
            True if successful
        """
        try:
            if not settings.cache_enabled:
                return False

            client = self._get_client()
            if client is None:
                return False

            json_value = json.dumps(value)
            ttl = ttl or settings.redis_cache_ttl

            client.setex(key, ttl, json_value)
            return True
        except Exception as e:
            print(f"Cache set failed for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        try:
            client = self._get_client()
            if client is None:
                return False

            client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete failed for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "instances:*")

        Returns:
            Number of keys deleted
        """
        try:
            client = self._get_client()
            if client is None:
                return 0

            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern failed for {pattern}: {e}")
            return 0


# Global cache manager instance
cache_manager = CacheManager()
