"""Rate limiting engine supporting Redis with thread-safe in-memory sliding window fallback."""
from datetime import datetime, timezone
import hashlib
import logging
import threading
import time
from typing import Optional, Dict, Tuple
from fastapi import Request, Response, HTTPException, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client = None
_redis_checked = False
_memory_lock = threading.Lock()
# Structure: { key: [(timestamp_float)] }
_memory_storage: Dict[str, list] = {}


def get_redis_client():
    """Get active Redis client if available and reachable."""
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client

    try:
        import redis
        client = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=0.5, socket_connect_timeout=0.5)
        client.ping()
        _redis_client = client
        logger.info("[OK] Redis rate limiter connected successfully.")
    except Exception as e:
        logger.warning(f"[INFO] Redis not reachable ({e}). Falling back to in-memory rate limiter.")
        _redis_client = None
    finally:
        _redis_checked = True

    return _redis_client


def _get_client_key(request: Request, prefix: str) -> str:
    """Derive unique client key using Bearer auth token if present, or client IP."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        hashed = hashlib.sha256(token.encode()).hexdigest()[:16]
        return f"{prefix}:auth:{hashed}"

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return f"{prefix}:ip:{client_ip}"


def _check_memory_rate_limit(key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
    """
    Check sliding window rate limit using in-memory store.
    Returns: (is_allowed, remaining_requests, retry_after_seconds)
    """
    now = time.time()
    cutoff = now - window_seconds

    with _memory_lock:
        timestamps = _memory_storage.setdefault(key, [])
        # Prune expired timestamps
        valid_timestamps = [ts for ts in timestamps if ts > cutoff]
        _memory_storage[key] = valid_timestamps

        count = len(valid_timestamps)
        if count >= max_requests:
            oldest = valid_timestamps[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, 0, retry_after

        valid_timestamps.append(now)
        remaining = max_requests - len(valid_timestamps)
        return True, remaining, 0


def _check_redis_rate_limit(redis_client, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
    """
    Check rate limit using Redis atomic multi-exec.
    Returns: (is_allowed, remaining_requests, retry_after_seconds)
    """
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        results = pipe.execute()
        current_count = results[0]
        ttl = results[1]

        if ttl == -1 or ttl is None:
            redis_client.expire(key, window_seconds)
            ttl = window_seconds

        if current_count > max_requests:
            retry_after = max(1, ttl if ttl > 0 else window_seconds)
            return False, 0, retry_after

        remaining = max(0, max_requests - current_count)
        return True, remaining, 0
    except Exception as e:
        logger.warning(f"Redis rate limit failed ({e}), falling back to memory.")
        return _check_memory_rate_limit(key, max_requests, window_seconds)


class RateLimiter:
    """FastAPI dependency to enforce rate limits per IP or authenticated user."""

    def __init__(self, requests: int = 60, window_seconds: int = 60, key_prefix: str = "rl"):
        self.requests = requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    async def __call__(self, request: Request, response: Response):
        # Bypass rate limits in test environments if specifically configured
        if getattr(settings, "ENVIRONMENT", "").lower() == "test_bypass_rl":
            return

        key = _get_client_key(request, self.key_prefix)
        redis_client = get_redis_client()

        if redis_client:
            is_allowed, remaining, retry_after = _check_redis_rate_limit(
                redis_client, key, self.requests, self.window_seconds
            )
        else:
            is_allowed, remaining, retry_after = _check_memory_rate_limit(
                key, self.requests, self.window_seconds
            )

        # Set standard rate limiting telemetry headers
        reset_time = int(time.time()) + (retry_after if retry_after > 0 else self.window_seconds)
        response.headers["X-RateLimit-Limit"] = str(self.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: Maximum {self.requests} requests per {self.window_seconds}s.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                }
            )
