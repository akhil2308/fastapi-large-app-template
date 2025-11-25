from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

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
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token, JWTConfig.SECRET_KEY, algorithms=[JWTConfig.ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None
