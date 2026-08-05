import redis
import logging
import os
from app.core.config import settings

logger = logging.getLogger("texlify.cache")

_redis_client = None


def get_redis() -> redis.Redis | None:
    """Return Redis client, or None if Redis is not available."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL")
        if not url:
            return None
        _redis_client = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _redis_client.ping()
        logger.info("Redis connected: %s", url.split("@")[-1])
        return _redis_client
    except Exception as e:
        logger.warning("Redis unavailable (%s) — running without cache", e)
        _redis_client = None
        return None


def cache_get(key: str) -> str | None:
    r = get_redis()
    if not r:
        return None
    try:
        return r.get(key)
    except Exception as e:
        logger.warning("Cache get failed: %s", e)
        return None


def cache_set(key: str, value: str, ttl_seconds: int = 300):
    r = get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl_seconds, value)
    except Exception as e:
        logger.warning("Cache set failed: %s", e)


def cache_delete(key: str):
    r = get_redis()
    if not r:
        return
    try:
        r.delete(key)
    except Exception as e:
        logger.warning("Cache delete failed: %s", e)


def cache_delete_pattern(pattern: str):
    """Delete all keys matching a pattern e.g. 'preview:42:*'"""
    r = get_redis()
    if not r:
        return
    try:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception as e:
        logger.warning("Cache delete pattern failed: %s", e)