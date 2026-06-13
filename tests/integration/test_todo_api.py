"""
Integration tests for todo API endpoints.

Tests cover:
- Todo CRUD operations
- Authentication required
- Rate limiting
"""

import uuid

import pytest
from httpx import AsyncClient

from app.core.auth import create_access_token
from tests.factories import (
    TodoCreateRequestFactory,
    TodoFactory,
    TokenFactory,
    UserFactory,
)


@pytest.mark.integration
class TestCreateTodo:
    """Tests for todo creation endpoint."""

    async def test_create_todo_success(self, client: AsyncClient, test_db):
        """Test successful todo creation."""
        # Create user and get token using factory
        _user, token = await TokenFactory.create_for_user(test_db)

        # Create todo using factory
        todo_data = TodoCreateRequestFactory.create()
        response = await client.post(
            "/api/v1/todo/",
            headers={"Authorization": f"Bearer {token}"},
            json=todo_data.model_dump(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Todo created successfully"
        assert data["data"]["title"] == todo_data.title

    async def test_create_todo_unauthenticated(self, client: AsyncClient):
        """Test creating todo without authentication."""
        response = await client.post("/api/v1/todo/", json={"title": "Test Todo"})

        assert response.status_code == 401

    async def test_create_todo_invalid_data(self, client: AsyncClient, test_db):
        """Test creating todo with invalid data."""
        # Create user and get token using factory
        _user, token = await TokenFactory.create_for_user(test_db)

        # Create todo with empty title
        response = await client.post(
            "/api/v1/todo/",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": ""},
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestGetTodos:
    """Tests for getting todos endpoint."""

    async def test_get_todos_success(self, client: AsyncClient, test_db):
        """Test successful getting todos."""
        # Create user with todos using factories
        user, token = await TokenFactory.create_for_user(test_db)
        # Type narrowing: user_id is guaranteed non-optional
        assert user.user_id is not None

        await TodoFactory.create_batch_async(
            db=test_db,
            user_id=user.user_id,
            count=3,
        )

        response = await client.get(
            "/api/v1/todo/", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 3

    async def test_get_todos_unauthenticated(self, client: AsyncClient):
        """Test getting todos without authentication."""
        response = await client.get("/api/v1/todo/")

        assert response.status_code == 401

    async def test_get_todos_pagination(self, client: AsyncClient, test_db):
        """Test todo pagination."""
        # Create user using factory
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )

        # Add 15 todos using factory
        for i in range(15):
            await TodoFactory.create_async(
                db=test_db,
                user_id=user.user_id,
                title=f"Todo {i}",
            )

        token = create_access_token(data={"sub": user.user_id})

        # Get first page
        response = await client.get(
            "/api/v1/todo/?page_number=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["total_size"] == 15
        assert data["total_pages"] == 3


@pytest.mark.integration
class TestUpdateTodo:
    """Tests for todo update endpoint."""

    async def test_update_todo_success(self, client: AsyncClient, test_db):
        """Test successful todo update."""
        # Create user and todo using factory
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )

        _todo = await TodoFactory.create_async(
            db=test_db,
            user_id=user.user_id,
            todo_id="test-todo-id",
            title="Original Title",
        )

        token = create_access_token(data={"sub": user.user_id})

        response = await client.put(
            "/api/v1/todo/test-todo-id",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Updated Title", "completed": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["title"] == "Updated Title"

    async def test_update_todo_not_found(self, client: AsyncClient, test_db):
        """Test updating non-existent todo."""
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )

        nonexistent_todo_id = str(uuid.uuid4())

        response = await client.put(
            f"/api/v1/todo/{nonexistent_todo_id}",
            headers={
                "Authorization": f"Bearer {create_access_token(data={'sub': user.user_id})}"
            },
            json={"title": "Updated Title"},
        )

        assert response.status_code == 404


@pytest.mark.integration
class TestDeleteTodo:
    """Tests for todo delete endpoint."""

    async def test_delete_todo_success(self, client: AsyncClient, test_db):
        """Test successful todo deletion (soft delete)."""
        # Create user and todo using factory
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )

        _todo = await TodoFactory.create_async(
            db=test_db,
            user_id=user.user_id,
            todo_id="test-todo-id",
            title="To Delete",
        )

        token = create_access_token(data={"sub": user.user_id})

        response = await client.delete(
            "/api/v1/todo/test-todo-id", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Todo deleted successfully"

    async def test_delete_todo_not_found(self, client: AsyncClient, test_db):
        """Test deleting non-existent todo."""
        # Create user using factory
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )

        nonexistent_todo_id = str(uuid.uuid4())

        response = await client.delete(
            f"/api/v1/todo/{nonexistent_todo_id}",
            headers={
                "Authorization": f"Bearer {create_access_token(data={'sub': user.user_id})}"
            },
        )

        assert response.status_code == 404


@pytest.mark.integration
class TestSoftDeleteSemantics:
    """Regression tests for P0.5 — soft-deleted todos must be invisible."""

    async def test_deleted_todo_not_in_list(self, client: AsyncClient, test_db):
        """A soft-deleted todo must not appear in the list endpoint."""
        user = await UserFactory.create_async(
            db=test_db, username="sduser1", email="sd1@example.com"
        )
        todo = await TodoFactory.create_async(
            db=test_db, user_id=user.user_id, todo_id="sd-todo-1", title="Will Delete"
        )
        token = create_access_token(data={"sub": user.user_id})

        del_resp = await client.delete(
            "/api/v1/todo/sd-todo-1", headers={"Authorization": f"Bearer {token}"}
        )
        assert del_resp.status_code == 200

        list_resp = await client.get(
            "/api/v1/todo/", headers={"Authorization": f"Bearer {token}"}
        )
        assert list_resp.status_code == 200
        ids = [t["todo_id"] for t in list_resp.json()["data"]]
        assert todo.todo_id not in ids

    async def test_deleted_todo_returns_404_on_update(
        self, client: AsyncClient, test_db
    ):
        """PUT on a soft-deleted todo must return 404."""
        user = await UserFactory.create_async(
            db=test_db, username="sduser2", email="sd2@example.com"
        )
        await TodoFactory.create_async(
            db=test_db, user_id=user.user_id, todo_id="sd-todo-2", title="Will Delete"
        )
        token = create_access_token(data={"sub": user.user_id})

        await client.delete(
            "/api/v1/todo/sd-todo-2", headers={"Authorization": f"Bearer {token}"}
        )

        put_resp = await client.put(
            "/api/v1/todo/sd-todo-2",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Resurrected"},
        )
        assert put_resp.status_code == 404

    async def test_re_delete_returns_404(self, client: AsyncClient, test_db):
        """DELETE on an already-deleted todo must return 404, not 200."""
        user = await UserFactory.create_async(
            db=test_db, username="sduser3", email="sd3@example.com"
        )
        await TodoFactory.create_async(
            db=test_db, user_id=user.user_id, todo_id="sd-todo-3", title="Will Delete"
        )
        token = create_access_token(data={"sub": user.user_id})

        first = await client.delete(
            "/api/v1/todo/sd-todo-3", headers={"Authorization": f"Bearer {token}"}
        )
        assert first.status_code == 200

        second = await client.delete(
            "/api/v1/todo/sd-todo-3", headers={"Authorization": f"Bearer {token}"}
        )
        assert second.status_code == 404

    async def test_deleted_todo_excluded_from_list(self, client: AsyncClient, test_db):
        """Soft-deleted todos must not appear in the list endpoint."""
        user = await UserFactory.create_async(
            db=test_db, username="sduser4", email="sd4@example.com"
        )
        todo = await TodoFactory.create_async(
            db=test_db, user_id=user.user_id, title="Listed Todo"
        )
        token = create_access_token(data={"sub": user.user_id})

        await client.delete(
            f"/api/v1/todo/{todo.todo_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        list_resp = await client.get(
            "/api/v1/todo/", headers={"Authorization": f"Bearer {token}"}
        )
        assert list_resp.status_code == 200
        assert list_resp.json()["total_size"] == 0


@pytest.mark.integration
class TestRefreshTokenRejected:
    """Regression test for P0.1 — refresh tokens must not work as access tokens."""

    async def test_refresh_token_rejected_on_todo_endpoint(
        self, client: AsyncClient, test_db
    ):
        """Using a refresh token as a Bearer token must return 401."""
        from app.core.auth import create_refresh_token

        user = await UserFactory.create_async(
            db=test_db, username="rtuser_int", email="rtint@example.com"
        )
        refresh_token = create_refresh_token(data={"sub": user.user_id})

        resp = await client.get(
            "/api/v1/todo/",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert resp.status_code == 401


@pytest.mark.integration
class TestUserIsolation:
    """Tests for user data isolation."""

    async def test_users_cannot_access_others_todos(self, client: AsyncClient, test_db):
        """Test that users can't access other users' todos."""
        # Create two users using factory
        user1 = await UserFactory.create_async(
            db=test_db,
            username="user1",
            email="user1@example.com",
        )
        user2 = await UserFactory.create_async(
            db=test_db,
            username="user2",
            email="user2@example.com",
        )

        # Add todo for user1
        await TodoFactory.create_async(
            db=test_db,
            user_id=user1.user_id,
            todo_id="user1-todo",
            title="User1's Todo",
        )

        # Try to access with user2's token
        token = create_access_token(data={"sub": user2.user_id})

        response = await client.get(
            "/api/v1/todo/", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # User2 should not see user1's todo
        assert all(todo["user_id"] != user1.user_id for todo in data["data"])
