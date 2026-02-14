"""
Pytest configuration and fixtures for the FastAPI application.

This module provides shared fixtures for:
- Database sessions with proper isolation
- Test client with mocked dependencies
- Authentication helpers
- Test data factories
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base
from app.main import app as main_app
from app.user.user_auth import create_access_token
from app.user.user_model import User
from tests.factories import (
    TodoFactory,
    TokenFactory,
    UserFactory,
)

# =============================================================================
# Test Configuration
# =============================================================================

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# =============================================================================
# Database Fixtures
# =============================================================================
@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session for testing.

    Each test gets a fresh database with all tables created.
    Tables are dropped after each test to ensure isolation.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide a session without wrapping in a transaction
    # This allows tests to commit/rollback as needed
    async with TestSessionLocal() as session:
        yield session

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# =============================================================================
# Test Client Fixtures
# =============================================================================
@pytest.fixture
def anyio_backend() -> str:
    """Specify the async backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an async HTTP client for API testing.

    The client is configured to use the FastAPI app with
    overridden dependencies for testing.
    """
    from app.core.database import get_db

    async def override_get_db():
        yield test_db

    main_app.dependency_overrides[get_db] = override_get_db

    # Mock Redis for rate limiting
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.evalsha = AsyncMock(return_value=0)
    main_app.state.redis = mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=main_app),  # type: ignore[arg-type]
        base_url="http://test",
    ) as ac:
        yield ac

    main_app.dependency_overrides.clear()


# =============================================================================
# User Fixtures
# =============================================================================
@pytest.fixture
def test_user_data() -> dict[str, str]:
    """Provides test user data."""
    return {
        "user_id": str(uuid.uuid4()),
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Creates a test user in the database using the factory."""
    return await UserFactory.create_async(db=test_db)


@pytest.fixture
async def test_user_with_todos(test_db: AsyncSession, test_user: User) -> User:
    """Creates a test user with sample todos using the factory."""
    # Type narrowing: user_id is guaranteed non-optional
    assert test_user.user_id is not None

    await TodoFactory.create_batch_async(
        db=test_db,
        user_id=test_user.user_id,
        count=3,
    )
    return test_user


# =============================================================================
# Authentication Fixtures
# =============================================================================
@pytest.fixture
def auth_token(test_user: User) -> str:
    """Generates a valid JWT token for the test user."""
    return create_access_token(data={"sub": test_user.user_id})


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Provides authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def expired_token(test_user: User) -> str:
    """Generates an expired JWT token."""
    return create_access_token(
        data={"sub": test_user.user_id},
        expires_delta=timedelta(seconds=-1),  # Already expired
    )


@pytest.fixture
def invalid_token() -> str:
    """Provides an invalid JWT token."""
    return "invalid.token.string"


# =============================================================================
# Factory-Based Convenience Fixtures
# =============================================================================
@pytest.fixture
async def authenticated_user(
    test_db: AsyncSession,
) -> tuple[User, str]:
    """
    Creates a user in DB and returns (user, token).

    Use this when you need both the user and a valid token.
    """
    return await TokenFactory.create_for_user(test_db)


@pytest.fixture
async def authenticated_headers(test_db: AsyncSession) -> dict[str, str]:
    """
    Creates a user in DB and returns auth headers.

    Use this for quick authenticated API calls.
    """
    _, headers = await TokenFactory.create_user_and_headers(test_db)
    return headers


@pytest.fixture
async def two_authenticated_users(
    test_db: AsyncSession,
) -> tuple[tuple[User, str], tuple[User, str]]:
    """
    Creates two separate users in DB with their tokens.

    Returns: ((user1, token1), (user2, token2))

    Use this for testing user isolation.
    """
    user1, token1 = await TokenFactory.create_for_user(
        test_db,
        username="user1",
        email="user1@example.com",
    )
    user2, token2 = await TokenFactory.create_for_user(
        test_db,
        username="user2",
        email="user2@example.com",
    )
    return (user1, token1), (user2, token2)


# =============================================================================
# Mock Fixtures
# =============================================================================
@pytest.fixture
def mock_redis() -> AsyncMock:
    """Provides a mock Redis client."""
    mock = AsyncMock()
    mock.ping = AsyncMock()
    mock.evalsha = AsyncMock(return_value=0)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    return mock


@pytest.fixture
def mock_rate_limiter():
    """Mocks the rate limiter to always allow requests."""
    with patch("app.utils.rate_limiter.FastAPILimiter") as mock:
        mock.redis = AsyncMock()
        mock.redis.evalsha = AsyncMock(return_value=0)
        mock.redis.ping = AsyncMock()
        mock.lua_sha = "test_sha"
        yield mock


# =============================================================================
# Helper Functions
# =============================================================================


# Note: Use factories from tests.factories instead of these helpers.
# The factories module provides:
#   - UserFactory.create_async(db, ...) for creating users in DB
#   - TodoFactory.create_async(db, user_id, ...) for creating todos in DB
#   - TokenFactory.create_for_user(db, ...) for creating users with tokens
# =============================================================================
# Pytest Configuration Hooks
# =============================================================================
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location."""
    for item in items:
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
