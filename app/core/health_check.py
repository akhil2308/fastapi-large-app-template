from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import AppConfig, DBConfig, RedisConfig


class ServiceUnavailableError(Exception):
    """
    Base exception for service unavailability.
    Used when a required service is not available at startup.
    """

    def __init__(self, service_name: str, message: str, help_text: str | None = None):
        self.service_name = service_name
        self.help_text = help_text
        super().__init__(message)


class RedisConnectionError(ServiceUnavailableError):
    """Raised when Redis is required but cannot be connected to."""

    def __init__(self, host: str, port: int, original_error: Exception):
        self.host = host
        self.port = port
        self.original_error = original_error

        message = f"Service unavailable: Redis at {host}:{port}"
        help_text = "Ensure Redis server is running. "

        super().__init__(service_name="Redis", message=message, help_text=help_text)


class DatabaseConnectionError(ServiceUnavailableError):
    """Raised when Database is required but cannot be connected to."""

    def __init__(self, host: str, port: int, database: str, original_error: Exception):
        self.host = host
        self.port = port
        self.database = database
        self.original_error = original_error

        message = f"Service unavailable: PostgreSQL at {host}:{port}/{database}"
        help_text = "Ensure PostgreSQL server is running and accessible. "

        super().__init__(
            service_name="PostgreSQL", message=message, help_text=help_text
        )


async def check_redis_health(redis: Redis) -> None:
    """
    Verify Redis connection is healthy.

    Args:
        redis: Redis client instance

    Raises:
        RedisConnectionError: If Redis is unavailable
    """
    try:
        await redis.ping()
    except Exception as e:
        await redis.close()
        raise RedisConnectionError(
            host=RedisConfig.HOST,
            port=RedisConfig.PORT,
            original_error=e,
        ) from e


async def check_database_health(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Verify database connection is healthy.

    Args:
        session_factory: SQLAlchemy async session factory

    Raises:
        DatabaseConnectionError: If database is unavailable
    """
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        raise DatabaseConnectionError(
            host=DBConfig.HOST,
            port=DBConfig.PORT,
            database=DBConfig.NAME,
            original_error=e,
        ) from e


def format_startup_error(
    error: ServiceUnavailableError, include_trace: bool = False
) -> str:
    """
    Format service unavailability error for startup failure message.

    The level of detail shown depends on AppConfig.DEBUG:
    - DEBUG=True: Full details with help text and traceback
    - DEBUG=False: Clean user-friendly message

    Args:
        error: ServiceUnavailableError instance
        include_trace: Force include traceback (overrides DEBUG setting)

    Returns:
        Formatted error message suitable for logging/display
    """
    # Show detailed info only in debug mode or when explicitly requested
    show_details = AppConfig.DEBUG or include_trace

    if show_details:
        lines = [
            f"ERROR: {error.service_name} is unavailable",
            f"  Reason: {str(error)}",
        ]

        if error.help_text:
            lines.append(f"  Fix: {error.help_text}")

        lines.append("")
        lines.append("Application cannot start without this service.")
    else:
        # Production-friendly message
        lines = [
            f"Service unavailable: {error.service_name}",
            "Please contact support or try again later.",
        ]

    return "\n".join(lines)
