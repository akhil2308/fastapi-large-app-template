import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi_limiter import FastAPILimiter  # type: ignore[attr-defined]
from jwt import PyJWTError

from app.core.settings import JWTConfig


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MIN
        )
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    encoded_jwt: str = jwt.encode(
        to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": datetime.now(UTC)
            + timedelta(days=JWTConfig.REFRESH_TOKEN_EXPIRE_DAYS),
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }
    )
    return jwt.encode(to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM]
        )
        return payload
    except PyJWTError:
        return None


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    payload = decode_access_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    if FastAPILimiter.redis is None:
        return
    await FastAPILimiter.redis.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    if FastAPILimiter.redis is None:
        return False
    return await FastAPILimiter.redis.exists(f"blacklist:{jti}") > 0
