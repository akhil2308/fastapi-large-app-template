"""
Unit tests for rate limiter functionality.

Tests cover:
- User-based rate limiting
- IP-based rate limiting
- Rate limit exceeded behavior
- Fail-open behavior when Redis is unavailable
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.utils.rate_limiter import ip_rate_limiter, user_rate_limiter


@pytest.mark.unit
class TestUserRateLimiter:
    """Tests for user_rate_limiter function."""

    async def test_allows_request_under_limit(self):
        """Test that requests under the limit are allowed."""
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=0)
            mock_limiter.prefix = "ratelimit"

            # Should not raise
            await user_rate_limiter(user_id="test-user", service="test-service")

    async def test_blocks_request_over_limit(self):
        """Test that requests over the limit are blocked."""
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=30000)  # 30 seconds
            mock_limiter.prefix = "ratelimit"

            with pytest.raises(HTTPException) as exc_info:
                await user_rate_limiter(user_id="test-user", service="test-service")

            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in exc_info.value.detail

    async def test_allows_when_redis_none(self):
        """Test that requests are allowed when Redis is not configured."""
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = None
            mock_limiter.prefix = "ratelimit"

            # Should not raise
            await user_rate_limiter(user_id="test-user", service="test-service")

    async def test_fail_open_on_redis_error(self):
        """Test that requests are allowed when Redis fails (fail-open)."""
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(side_effect=Exception("Redis down"))
            mock_limiter.prefix = "ratelimit"

            # Should not raise (fail-open behavior)
            await user_rate_limiter(user_id="test-user", service="test-service")

    async def test_custom_limits(self):
        """Test rate limiter with custom times and seconds."""
        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=0)
            mock_limiter.prefix = "ratelimit"

            # Should not raise
            await user_rate_limiter(
                user_id="test-user", service="test-service", times=10, seconds=30
            )


@pytest.mark.unit
class TestIPRateLimiter:
    """Tests for ip_rate_limiter function."""

    async def test_allows_request_under_limit(self):
        """Test that requests under the limit are allowed."""
        mock_request = Request(scope={"type": "http", "client": ("127.0.0.1", 12345)})

        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=0)
            mock_limiter.prefix = "ratelimit"

            # Should not raise
            await ip_rate_limiter(request=mock_request, service="test-service")

    async def test_blocks_request_over_limit(self):
        """Test that requests over the limit are blocked."""
        mock_request = Request(scope={"type": "http", "client": ("127.0.0.1", 12345)})

        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=30000)
            mock_limiter.prefix = "ratelimit"

            with pytest.raises(HTTPException) as exc_info:
                await ip_rate_limiter(request=mock_request, service="test-service")

            assert exc_info.value.status_code == 429

    async def test_allows_when_no_client_ip(self):
        """Test that requests are allowed when client IP is not available."""
        mock_request = Request(scope={"type": "http", "client": None})

        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(return_value=0)
            mock_limiter.prefix = "ratelimit"

            # Should not raise - uses 'unknown' as fallback
            await ip_rate_limiter(request=mock_request, service="test-service")

    async def test_fail_open_on_redis_error(self):
        """Test that requests are allowed when Redis fails (fail-open)."""
        mock_request = Request(scope={"type": "http", "client": ("127.0.0.1", 12345)})

        with patch("app.utils.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.redis = AsyncMock()
            mock_limiter.redis.evalsha = AsyncMock(side_effect=Exception("Redis down"))
            mock_limiter.prefix = "ratelimit"

            # Should not raise (fail-open behavior)
            await ip_rate_limiter(request=mock_request, service="test-service")
