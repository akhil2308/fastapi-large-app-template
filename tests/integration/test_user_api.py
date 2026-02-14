"""
Integration tests for user API endpoints.

Tests cover:
- User registration
- User login
- Authentication flow
"""

import pytest
from httpx import AsyncClient

from tests.factories import (
    UserCreateRequestFactory,
    UserFactory,
)


@pytest.mark.integration
class TestUserRegistration:
    """Tests for user registration endpoint."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = UserCreateRequestFactory.create()
        response = await client.post(
            "/api/v1/user/register",
            json=user_data.model_dump(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "User registered successfully"
        assert "data" in data

    async def test_register_duplicate_username(self, client: AsyncClient, test_db):
        """Test registration with duplicate username."""
        # Create existing user using factory
        await UserFactory.create_async(
            db=test_db,
            username="existinguser",
            email="existing@example.com",
        )

        # Try to register with same username
        response = await client.post(
            "/api/v1/user/register",
            json={
                "username": "existinguser",
                "email": "different@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/v1/user/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password."""
        response = await client.post(
            "/api/v1/user/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "short",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"


@pytest.mark.integration
class TestUserLogin:
    """Tests for user login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_db):
        """Test successful user login."""
        # Create user using factory with known password
        await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )

        # Login with factory's default password
        response = await client.post(
            "/api/v1/user/login",
            json={"username": "testuser", "password": "TestPass123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_db):
        """Test login with wrong password."""
        # Create user using factory
        await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # correctpassword
        )

        # Login with wrong password
        response = await client.post(
            "/api/v1/user/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/user/login",
            json={"username": "nonexistent", "password": "somepassword"},
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestAuthenticationFlow:
    """Tests for authentication flow."""

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/api/v1/todo/")

        assert response.status_code == 401

    async def test_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        response = await client.get(
            "/api/v1/todo/", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    async def test_full_auth_flow(self, client: AsyncClient):
        """Test complete authentication flow."""
        # 1. Register a new user
        register_response = await client.post(
            "/api/v1/user/register",
            json={
                "username": "flowuser",
                "email": "flow@example.com",
                "password": "SecurePass123!",
            },
        )
        assert register_response.status_code == 201

        # 2. Login
        login_response = await client.post(
            "/api/v1/user/login",
            json={"username": "flowuser", "password": "SecurePass123!"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        # 3. Access protected endpoint
        todo_response = await client.get(
            "/api/v1/todo/", headers={"Authorization": f"Bearer {token}"}
        )
        assert todo_response.status_code == 200
