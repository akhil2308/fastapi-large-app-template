from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.user.user_crud import create_user, get_user_by_username_or_email, get_user_by_username
from app.user.user_schema import UserCreateRequest


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def register_user(db: Session, user_create: UserCreateRequest):
    # Check if the username or email already exists
    if await get_user_by_username_or_email(db, user_create.username, user_create.email):
        return None 

    hashed = hash_password(user_create.password)
    user = await create_user(
        db,
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed
    )
    return UserCreateRequest.model_validate(user)


async def login_user(db: Session, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
