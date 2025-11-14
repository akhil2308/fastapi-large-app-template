from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.settings import DBConfig

# Use asyncpg driver for PostgreSQL async support
SQLALCHEMY_DATABASE_URL = DBConfig.ASYNC_URL

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=DBConfig.POOL_SIZE,
    max_overflow=DBConfig.MAX_OVERFLOW,
    pool_recycle=300,
    pool_pre_ping=True,
    future=True  # Enable SQLAlchemy 2.0 future APIs
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

# Async database dependency
async def get_db():
    """
    Async generator that yields database sessions
    Usage in endpoints: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception as e:
            await db.rollback()
            raise
        finally:
            await db.close()