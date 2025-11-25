import logging
from math import ceil

from fastapi import HTTPException, status
from fastapi_limiter import FastAPILimiter

logger = logging.getLogger(__name__)


async def user_rate_limiter(
    user_id: str, service: str, times: int = 5, seconds: int = 60
):
    """
    Custom rate limiting dependency using FastAPILimiter's Lua script.
    Uses the authenticated user's ID to build a unique key.
    If Redis fails, logs the error and allows the request to proceed.
    """
    milliseconds = seconds * 1000
    key = f"{FastAPILimiter.prefix}:user:{user_id}:{service}"

    try:
        if FastAPILimiter.redis is None:
            return

        pexpire = await FastAPILimiter.redis.evalsha(
            FastAPILimiter.lua_sha, 1, key, str(times), str(milliseconds)
        )
    except Exception as e:
        logger.error(f"Rate limiting check failed: {e}. Allowing request to proceed.")
        pexpire = 0  # Allow request to pass if redis is down

    # If pexpire is nonzero, rate limit has been exceeded.
    if pexpire != 0:
        expire_seconds = ceil(pexpire / 1000)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {expire_seconds} seconds.",
        )
