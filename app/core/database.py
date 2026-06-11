from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.settings import settings

# Use asyncpg driver for PostgreSQL async support
SQLALCHEMY_DATABASE_URL = settings.db.async_url

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_recycle=300,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False, autocommit=False
)

Base = declarative_base()


# Async database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields database sessions
    Usage in endpoints: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()
