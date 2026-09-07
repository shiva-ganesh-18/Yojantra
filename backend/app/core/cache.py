"""Resilient caching module with dual Redis and in-memory fallback.
Ensures zero-crash execution whether Redis is running or unavailable.
"""
import json
import time
from typing import Optional, Any
from app.core.config import get_settings

settings = get_settings()

_redis_client = None
_in_memory_cache: dict[str, tuple[Any, float]] = {}


def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis
        client = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
            decode_responses=True
        )
        # Test connection
        client.ping()
        _redis_client = client
    except Exception:
        _redis_client = False  # Mark as unavailable

    return _redis_client


class CacheClient:
    """Unified cache interface with transparent Redis / In-Memory switching."""

    @property
    def is_redis_available(self) -> bool:
        client = _get_redis_client()
        return client is not False and client is not None

    def get(self, key: str) -> Optional[Any]:
        client = _get_redis_client()
        if client:
            try:
                val = client.get(key)
                if val is not None:
                    return json.loads(val)
                return None
            except Exception:
                pass

        # In-memory fallback
        if key in _in_memory_cache:
            data, expiry = _in_memory_cache[key]
            if expiry == 0 or time.time() < expiry:
                return data
            else:
                del _in_memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        client = _get_redis_client()
        serialized = json.dumps(value, default=str)
        if client:
            try:
                client.setex(key, ttl_seconds, serialized)
                return True
            except Exception:
                pass

        # In-memory fallback
        expiry = time.time() + ttl_seconds if ttl_seconds > 0 else 0
        _in_memory_cache[key] = (value, expiry)
        return True

    def delete(self, key: str) -> bool:
        client = _get_redis_client()
        if client:
            try:
                client.delete(key)
            except Exception:
                pass
        _in_memory_cache.pop(key, None)
        return True

    def ping(self) -> bool:
        """Returns True if Redis is reachable, False if running on in-memory fallback."""
        client = _get_redis_client()
        if client:
            try:
                return bool(client.ping())
            except Exception:
                return False
        return False


_cache_instance = CacheClient()


def get_cache() -> CacheClient:
    """Get the singleton cache client."""
    return _cache_instance
