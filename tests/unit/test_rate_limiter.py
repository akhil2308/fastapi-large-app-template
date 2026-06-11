"""
Unit tests for rate limiter functionality.

Tests cover:
- User-scoped rate limiting dependency
- IP-scoped rate limiting dependency
- Rate limit exceeded behavior
- Fail-open behavior when Redis is unavailable
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.utils.rate_limiter import RateLimit

USER = SimpleNamespace(user_id="test-user")


@pytest.mark.unit
class TestUserRateLimit:
    """Tests for the user-scoped RateLimit dependency."""

    async def test_allows_request_under_limit(self):
        dependency = RateLimit("test-service", scope="user")
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=0)
            mock_limiter.prefix = "ratelimit"

            # Should not raise
            await dependency(current_user=USER)

    async def test_blocks_request_over_limit(self):
        dependency = RateLimit("test-service", scope="user")
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=30000)  # 30 seconds
            mock_limiter.prefix = "ratelimit"

            with pytest.raises(HTTPException) as exc_info:
                await dependency(current_user=USER)

            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in exc_info.value.detail

    async def test_allows_when_redis_none(self):
        dependency = RateLimit("test-service", scope="user")
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = None
            mock_limiter.prefix = "ratelimit"

            # Should not raise
            await dependency(current_user=USER)

    async def test_fail_open_on_redis_error(self):
        dependency = RateLimit("test-service", scope="user")
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(side_effect=Exception("Redis down"))
            mock_limiter.prefix = "ratelimit"

            # Should not raise (fail-open behavior)
            await dependency(current_user=USER)


@pytest.mark.unit
class TestIPRateLimit:
    """Tests for the ip-scoped RateLimit dependency."""

    async def test_allows_request_under_limit(self):
        dependency = RateLimit("test-service", scope="ip")
        request = Request(scope={"type": "http", "client": ("127.0.0.1", 12345)})
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=0)
            mock_limiter.prefix = "ratelimit"

            # Should not raise
            await dependency(request=request)

    async def test_blocks_request_over_limit(self):
        dependency = RateLimit("test-service", scope="ip")
        request = Request(scope={"type": "http", "client": ("127.0.0.1", 12345)})
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=30000)
            mock_limiter.prefix = "ratelimit"

            with pytest.raises(HTTPException) as exc_info:
                await dependency(request=request)

            assert exc_info.value.status_code == 429

    async def test_allows_when_no_client_ip(self):
        dependency = RateLimit("test-service", scope="ip")
        request = Request(scope={"type": "http", "client": None})
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=0)
            mock_limiter.prefix = "ratelimit"

            # Should not raise - uses 'unknown' as fallback
            await dependency(request=request)

    async def test_fail_open_on_redis_error(self):
        dependency = RateLimit("test-service", scope="ip")
        request = Request(scope={"type": "http", "client": ("127.0.0.1", 12345)})
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(side_effect=Exception("Redis down"))
            mock_limiter.prefix = "ratelimit"

            # Should not raise (fail-open behavior)
            await dependency(request=request)
