import logging
from collections.abc import Awaitable, Callable
from math import ceil
from typing import Literal

from fastapi import Depends, HTTPException, Request, status
from fastapi_limiter import FastAPILimiter  # type: ignore[attr-defined]

from app.api.deps import get_current_user
from app.models.user_model import User
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


def RateLimit(
    service: str,
    scope: Literal["user", "ip"] = "user",
    per_min: int = 5,
) -> Callable[..., Awaitable[None]]:
    """Build a rate-limit dependency keyed by the authenticated user or the client IP.

    Declare it on a route via ``dependencies=[Depends(RateLimit(...))]`` so the
    limit is visible in the route definition (and its 429 in the OpenAPI docs).
    """
    if scope == "user":

        async def user_dependency(
            current_user: User = Depends(get_current_user),
        ) -> None:
            key = f"{FastAPILimiter.prefix}:user:{current_user.user_id}:{service}"
            await _execute_rate_limit(key, per_min, 60, service)

        return user_dependency

    async def ip_dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{FastAPILimiter.prefix}:ip:{client_ip}:{service}"
        await _execute_rate_limit(key, per_min, 60, service)

    return ip_dependency
