from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.user.user_crud import (
    create_user,
    get_user_by_username,
    get_user_by_username_or_email,
)
from app.user.user_model import User
from app.user.user_schema import UserCreateRequest, UserCreateResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    hashed: str = pwd_context.hash(password)
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result


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
    if not user or user.hashed_password is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Invalid credentials")
    return user
