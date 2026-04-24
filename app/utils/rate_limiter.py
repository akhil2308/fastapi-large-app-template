import logging
from math import ceil

from fastapi import HTTPException, Request, status
from fastapi_limiter import FastAPILimiter  # type: ignore[attr-defined]

from app.observability.metrics import (
    record_ratelimit_decision,
    record_ratelimit_degraded,
)

logger = logging.getLogger(__name__)


async def _execute_rate_limit(key: str, times: int, seconds: int, service: str) -> None:
    milliseconds = seconds * 1000
    rate_limit_executed = True
    try:
        if FastAPILimiter.redis is None:
            return

        pexpire = await FastAPILimiter.redis.evalsha(
            FastAPILimiter.lua_sha, 1, key, str(times), str(milliseconds)
        )
    except Exception as e:
        logger.error(f"Rate limiting check failed: {e}. Allowing request to proceed.")
        pexpire = 0
        rate_limit_executed = False
        record_ratelimit_degraded(service)

    if rate_limit_executed:
        if pexpire != 0:
            expire_seconds = ceil(pexpire / 1000)
            record_ratelimit_decision(allowed=False, service=service)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {expire_seconds} seconds.",
            )
        record_ratelimit_decision(allowed=True, service=service)


async def user_rate_limiter(
    user_id: str, service: str, times: int = 5, seconds: int = 60
) -> None:
    key = f"{FastAPILimiter.prefix}:user:{user_id}:{service}"
    await _execute_rate_limit(key, times, seconds, service)


async def ip_rate_limiter(
    request: Request, service: str, times: int = 5, seconds: int = 60
) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{FastAPILimiter.prefix}:ip:{client_ip}:{service}"
    await _execute_rate_limit(key, times, seconds, service)
