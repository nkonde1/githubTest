# backend/app/redis_client.py
"""
Async Redis client factory and type alias used by the backend.
Provides:
 - get_redis() -> returns a redis.asyncio.Redis instance (create-on-first-use)
 - RedisClient -> alias for the redis.asyncio.Redis class for typing/import compatibility
"""

import os
import logging
from typing import Optional, Any
import json

import redis.asyncio as aioredis

# Try to import project settings; fall back to environment
try:
    from app.core.config import settings
    REDIS_URL = getattr(settings, "REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
except Exception:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Small async wrapper that provides an `init()` used by app.main,
    and forwards common async list/string operations to redis.asyncio.Redis.
    Call `await redis_client.init()` at startup (app.main expects this).
    """
    def __init__(self, url: str = REDIS_URL):
        self.url = url
        self._client: Optional[aioredis.Redis] = None
        self._initialized: bool = False

    async def init(self) -> None:
        if self._client is None:
            logger.info("Creating async Redis client: %s", self.url)
            self._client = aioredis.from_url(self.url, decode_responses=True)
        self._initialized = True

    def _ensure_client(self) -> aioredis.Redis:
        if self._client is None:
            # create lazily if init() wasn't awaited; still works
            self._client = aioredis.from_url(self.url, decode_responses=True)
        return self._client

    # List operations (async)
    async def lrange(self, key: str, start: int, stop: int) -> list:
        return await self._ensure_client().lrange(key, start, stop)

    async def lpush(self, key: str, *values: Any) -> int:
        return await self._ensure_client().lpush(key, *values)

    # String / key operations
    async def set(self, key: str, value: Any, **kwargs) -> bool:
        return await self._ensure_client().set(key, value, **kwargs)

    async def get(self, key: str) -> Optional[str]:
        return await self._ensure_client().get(key)

    async def delete(self, key: str) -> int:
        return await self._ensure_client().delete(key)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._initialized = False

    async def get_user_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve user session data from Redis by session ID.
        :param session_id: The ID of the session to retrieve.
        :return: The session data as a dictionary, or None if not found.
        """
        session_data = await self.get(session_id)
        if session_data:
            return json.loads(session_data)  # Assuming session data is stored as JSON
        return None

    async def set_user_session(self, session_id: str, user_data: dict, expires_in: int) -> None:
        """Store user session data as JSON with an expiration."""
        try:
            await self.set(session_id, json.dumps(user_data), ex=expires_in)
        except Exception as e:
            logger.warning("Failed to set user session in Redis: %s", e)

    async def rate_limit_check(self, identifier: str, requests: int, window: int):
        """
        Simple token-bucket style rate limit using Redis INCR/EXPIRE.
        Returns tuple (allowed: bool, remaining: int). If Redis is unavailable,
        allow the request.
        """
        key = f"rate:{identifier}:{window}"
        try:
            client = self._ensure_client()
            current = await client.incr(key)
            if current == 1:
                await client.expire(key, window)
            remaining = max(0, requests - current)
            return current <= requests, remaining
        except Exception as e:
            logger.warning("Rate limit check skipped (Redis unavailable): %s", e)
            return True, requests


# module-level instance + helper for existing imports
_redis_instance: RedisClient = RedisClient()
def get_redis() -> RedisClient:
    return _redis_instance

# convenience name used across the codebase
redis_client = get_redis()

# NOTE: Do NOT alias RedisClient to aioredis.Redis here; we intentionally
# export the wrapper class above so callers can access helper methods.