import logging
from math import ceil

from fastapi import HTTPException, Request, status
from fastapi_limiter import FastAPILimiter  # type: ignore[attr-defined]

from app.observability.metrics import (
    record_ratelimit_decision,
    record_ratelimit_degraded,
)

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

    rate_limit_executed = True
    try:
        if FastAPILimiter.redis is None:
            return

        pexpire = await FastAPILimiter.redis.evalsha(
            FastAPILimiter.lua_sha, 1, key, str(times), str(milliseconds)
        )
    except Exception as e:
        logger.error(f"Rate limiting check failed: {e}. Allowing request to proceed.")
        pexpire = 0  # Allow request to pass if redis is down
        rate_limit_executed = False  # Mark that we didn't actually rate limit
        record_ratelimit_degraded(service)  # Track fail-open

    # Only record metrics if rate limiting was actually attempted
    if rate_limit_executed:
        # If pexpire is nonzero, rate limit has been exceeded.
        if pexpire != 0:
            expire_seconds = ceil(pexpire / 1000)
            record_ratelimit_decision(allowed=False, service=service)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {expire_seconds} seconds.",
            )

        record_ratelimit_decision(allowed=True, service=service)


async def ip_rate_limiter(
    request: Request, service: str, times: int = 5, seconds: int = 60
):
    """
    IP-based rate limiting for endpoints without authentication.
    Uses the client's IP address to build a unique key.
    If Redis fails, logs the error and allows the request to proceed.
    """
    milliseconds = seconds * 1000
    # Get client IP, fallback to 'unknown' if not available
    client_ip = request.client.host if request.client else "unknown"
    key = f"{FastAPILimiter.prefix}:ip:{client_ip}:{service}"

    rate_limit_executed = True
    try:
        if FastAPILimiter.redis is None:
            return

        pexpire = await FastAPILimiter.redis.evalsha(
            FastAPILimiter.lua_sha, 1, key, str(times), str(milliseconds)
        )
    except Exception as e:
        logger.error(f"Rate limiting check failed: {e}. Allowing request to proceed.")
        pexpire = 0  # Allow request to pass if redis is down
        rate_limit_executed = False  # Mark that we didn't actually rate limit
        record_ratelimit_degraded(service)  # Track fail-open

    # Only record metrics if rate limiting was actually attempted
    if rate_limit_executed:
        # If pexpire is nonzero, rate limit has been exceeded.
        if pexpire != 0:
            expire_seconds = ceil(pexpire / 1000)
            record_ratelimit_decision(allowed=False, service=service)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {expire_seconds} seconds.",
            )

        record_ratelimit_decision(allowed=True, service=service)
