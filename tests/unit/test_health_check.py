"""
Unit tests for startup health checks.

Tests cover:
- Redis connectivity check
- Database connectivity check
- Startup error formatting
"""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.health_check import (
    DatabaseConnectionError,
    RedisConnectionError,
    check_database_health,
    check_redis_health,
    format_startup_error,
)


@pytest.mark.unit
class TestCheckRedisHealth:
    """Tests for check_redis_health."""

    async def test_healthy_redis_passes(self, fake_redis):
        """A reachable Redis does not raise."""
        await check_redis_health(fake_redis)

    async def test_unreachable_redis_raises(self):
        """A failing ping raises RedisConnectionError and closes the client."""
        redis = AsyncMock()
        redis.ping = AsyncMock(side_effect=ConnectionError("down"))

        with pytest.raises(RedisConnectionError):
            await check_redis_health(redis)
        redis.close.assert_awaited_once()


@pytest.mark.unit
class TestCheckDatabaseHealth:
    """Tests for check_database_health."""

    async def test_healthy_database_passes(self):
        """A working session factory does not raise."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        factory = async_sessionmaker(bind=engine)

        await check_database_health(factory)
        await engine.dispose()

    async def test_unreachable_database_raises(self):
        """A session factory that fails raises DatabaseConnectionError."""

        def factory():
            raise OSError("no socket")

        with pytest.raises(DatabaseConnectionError):
            await check_database_health(factory)  # type: ignore[arg-type]


@pytest.mark.unit
class TestFormatStartupError:
    """Tests for format_startup_error."""

    def test_debug_includes_details(self, monkeypatch):
        """Debug mode surfaces the reason and fix help text."""
        from app.core.settings import settings

        monkeypatch.setattr(settings.app, "debug", True)
        error = RedisConnectionError("localhost", 6379, ConnectionError("x"))

        message = format_startup_error(error)

        assert "Redis is unavailable" in message
        assert "Fix:" in message

    def test_production_hides_details(self, monkeypatch):
        """Non-debug mode shows a clean user-facing message."""
        from app.core.settings import settings

        monkeypatch.setattr(settings.app, "debug", False)
        error = RedisConnectionError("localhost", 6379, ConnectionError("x"))

        message = format_startup_error(error)

        assert "Service unavailable: Redis" in message
        assert "Fix:" not in message
