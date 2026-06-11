import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import PyJWTError
from redis.asyncio import Redis

from app.core.settings import settings


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4()), "type": "access"})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": datetime.now(UTC)
            + timedelta(days=settings.jwt.refresh_token_expire_days),
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }
    )
    return jwt.encode(
        to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm]
        )
        return payload
    except PyJWTError:
        return None


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    payload = decode_access_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


async def blacklist_token(redis: Redis, jti: str, ttl_seconds: int) -> None:
    if redis is None:
        return
    await redis.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_token_blacklisted(redis: Redis, jti: str) -> bool:
    if redis is None:
        return False
    return await redis.exists(f"blacklist:{jti}") > 0
