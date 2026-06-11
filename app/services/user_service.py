from datetime import UTC, datetime

from pwdlib import PasswordHash
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    is_token_blacklisted,
)
from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.crud.user_crud import (
    create_user,
    get_user_by_user_id,
    get_user_by_username,
    get_user_by_username_or_email,
)
from app.models.user_model import User
from app.schemas.user_schema import TokenPair, UserCreateRequest, UserCreateResponse

_pwd = PasswordHash.recommended()
# Used on the login miss-path so response time is constant regardless of username existence.
_DUMMY_HASH: str = _pwd.hash("__dummy__")


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd.verify(plain_password, hashed_password)


async def register_user(
    db: AsyncSession, user_create: UserCreateRequest
) -> UserCreateResponse:
    if await get_user_by_username_or_email(db, user_create.username, user_create.email):
        raise UserAlreadyExistsError("Username or email already exists")

    hashed = hash_password(user_create.password)
    user = await create_user(
        db,
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed,
    )
    return UserCreateResponse.model_validate(user)


async def login_user(db: AsyncSession, username: str, password: str) -> User:
    user = await get_user_by_username(db, username)
    if not user:
        verify_password(
            password, _DUMMY_HASH
        )  # constant-time: prevent username enumeration
        raise InvalidCredentialsError("Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Invalid credentials")
    return user


async def logout_user(redis: Redis, token: str) -> None:
    payload = decode_access_token(token)
    if payload and (jti := payload.get("jti")):
        ttl = int(payload["exp"] - datetime.now(UTC).timestamp())
        if ttl > 0:
            await blacklist_token(redis, jti, ttl)


async def refresh_tokens(
    db: AsyncSession, redis: Redis, refresh_token: str
) -> TokenPair:
    # Trade-offs: JTI blacklisting does not cover family reuse (stolen token
    # rotated first); is_token_blacklisted fails open when Redis is down
    # (deliberate: availability > strict revocation — see app/core/auth.py).
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise InvalidCredentialsError("Invalid or expired refresh token")

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(redis, jti):
        raise InvalidCredentialsError("Refresh token has been revoked")

    user = await get_user_by_user_id(db, payload["sub"])
    if not user:
        raise InvalidCredentialsError("User not found")

    if jti:
        ttl = int(payload["exp"] - datetime.now(UTC).timestamp())
        if ttl > 0:
            await blacklist_token(redis, jti, ttl)

    return TokenPair(
        access_token=create_access_token({"sub": user.user_id}),
        refresh_token=create_refresh_token({"sub": user.user_id}),
    )
