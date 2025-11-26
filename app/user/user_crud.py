import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.user_model import User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    return (await db.scalars(select(User).where(User.username == username))).first()


async def get_user_by_username_or_email(
    db: AsyncSession, username: str | None = None, email: str | None = None
) -> User | None:
    result = await db.execute(
        select(User).where(or_(User.username == username, User.email == email))
    )
    return result.scalars().first()


async def get_user_by_user_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalars().first()


async def create_user(
    db: AsyncSession, username: str, email: str, hashed_password: str
) -> User:
    user = User(
        user_id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
