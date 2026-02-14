"""
End-to-end tests for complete user flows.

Tests cover:
- Complete user journeys
- Multiple user scenarios
- Error handling flows
"""

import uuid

import pytest
from httpx import AsyncClient

from app.user.user_auth import create_access_token
from tests.factories import TokenFactory, UserFactory


@pytest.mark.e2e
class TestUserRegistrationToTodoFlow:
    """Test complete user journey from registration to todo management."""

    async def test_full_user_journey(self, client: AsyncClient):
        """Test complete user journey: register -> login -> create todo -> get todos -> update -> delete."""
        # Step 1: Register a new user
        register_response = await client.post(
            "/api/v1/user/register",
            json={
                "username": "journeyuser",
                "email": "journey@example.com",
                "password": "SecurePass123!",
            },
        )
        assert register_response.status_code == 201
        # User data from registration
        register_response.json()["data"]

        # Step 2: Login
        login_response = await client.post(
            "/api/v1/user/login",
            json={"username": "journeyuser", "password": "SecurePass123!"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: Create first todo
        create_response1 = await client.post(
            "/api/v1/todo/",
            headers=headers,
            json={"title": "First Todo", "description": "My first task"},
        )
        assert create_response1.status_code == 201
        todo1_id = create_response1.json()["data"]["todo_id"]

        # Step 4: Create second todo
        create_response2 = await client.post(
            "/api/v1/todo/", headers=headers, json={"title": "Second Todo"}
        )
        assert create_response2.status_code == 201

        # Step 5: Get all todos
        get_response = await client.get("/api/v1/todo/", headers=headers)
        assert get_response.status_code == 200
        todos = get_response.json()["data"]
        assert len(todos) == 2

        # Step 6: Update first todo
        update_response = await client.put(
            f"/api/v1/todo/{todo1_id}",
            headers=headers,
            json={"title": "Updated First Todo", "completed": True},
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["completed"] is True

        # Step 7: Delete second todo
        delete_response = await client.delete(
            f"/api/v1/todo/{create_response2.json()['data']['todo_id']}",
            headers=headers,
        )
        assert delete_response.status_code == 200

        # Step 8: Verify final state
        final_response = await client.get("/api/v1/todo/", headers=headers)
        final_todos = final_response.json()["data"]
        assert len(final_todos) == 1
        assert final_todos[0]["title"] == "Updated First Todo"


@pytest.mark.e2e
class TestMultipleUsersIsolation:
    """Test that multiple users can't access each other's data."""

    async def test_users_data_isolation(self, client: AsyncClient, test_db):
        """Test complete isolation between users."""
        # Create two users with tokens using factory
        (_user1, token1), (_user2, token2) = (
            await TokenFactory.create_for_user(
                test_db,
                username="alice",
                email="alice@example.com",
            ),
            await TokenFactory.create_for_user(
                test_db,
                username="bob",
                email="bob@example.com",
            ),
        )

        # User 1 creates todos
        await client.post(
            "/api/v1/todo/",
            headers={"Authorization": f"Bearer {token1}"},
            json={"title": "Alice's Todo 1"},
        )
        await client.post(
            "/api/v1/todo/",
            headers={"Authorization": f"Bearer {token1}"},
            json={"title": "Alice's Todo 2"},
        )

        # User 2 creates todos
        await client.post(
            "/api/v1/todo/",
            headers={"Authorization": f"Bearer {token2}"},
            json={"title": "Bob's Todo 1"},
        )
        await client.post(
            "/api/v1/todo/",
            headers={"Authorization": f"Bearer {token2}"},
            json={"title": "Bob's Todo 2"},
        )
        await client.post(
            "/api/v1/todo/",
            headers={"Authorization": f"Bearer {token2}"},
            json={"title": "Bob's Todo 3"},
        )

        # Verify User 1 sees only their todos
        response1 = await client.get(
            "/api/v1/todo/", headers={"Authorization": f"Bearer {token1}"}
        )
        todos1 = response1.json()["data"]
        assert len(todos1) == 2
        assert all("Alice" in t["title"] for t in todos1)

        # Verify User 2 sees only their todos
        response2 = await client.get(
            "/api/v1/todo/", headers={"Authorization": f"Bearer {token2}"}
        )
        todos2 = response2.json()["data"]
        assert len(todos2) == 3
        assert all("Bob" in t["title"] for t in todos2)

        # Verify cross-user access is blocked
        # Try to update Alice's todo with Bob's token
        alice_todo_id = todos1[0]["todo_id"]
        update_response = await client.put(
            f"/api/v1/todo/{alice_todo_id}",
            headers={"Authorization": f"Bearer {token2}"},
            json={"title": "Hacked!"},
        )
        # Should return 404 because Bob can't see Alice's todo
        assert update_response.status_code == 404


@pytest.mark.e2e
class TestErrorHandlingFlows:
    """Test error handling across the application."""

    async def test_validation_error_format(self, client: AsyncClient):
        """Test that validation errors return consistent format."""
        response = await client.post(
            "/api/v1/user/register",
            json={"username": "test", "email": "invalid", "password": "short"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"
        assert "message" in data
        assert "errors" in data

    async def test_authentication_error_format(self, client: AsyncClient):
        """Test that auth errors return consistent format."""
        response = await client.get(
            "/api/v1/todo/", headers={"Authorization": "Bearer invalid"}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"

    async def test_not_found_error_format(self, client: AsyncClient, test_db):
        """Test that not found errors return consistent format."""
        # Create user using factory
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )

        token = create_access_token(data={"sub": user.user_id})

        # Use a valid UUID format that doesn't exist
        nonexistent_uuid = str(uuid.uuid4())
        response = await client.put(
            f"/api/v1/todo/{nonexistent_uuid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Updated Todo"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"


@pytest.mark.e2e
class TestHealthCheck:
    """Test health check endpoint."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/api/v1/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
