"""
Test data factories for creating consistent test data.

This module provides factory classes for generating test data
following the factory boy pattern.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.todo.todo_schema import TodoCreate, TodoUpdate
from app.user.user_schema import UserCreateRequest

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.todo.todo_model import Todo
    from app.user.user_model import User


# =============================================================================
# User Factories
# =============================================================================
class UserFactory:
    """Factory for creating User model data."""

    @staticmethod
    def build(**kwargs: Any) -> dict[str, Any]:
        """
        Build user data dictionary with default values.

        Args:
            **kwargs: Override default values

        Returns:
            Dictionary with user data
        """
        defaults = {
            "user_id": str(uuid.uuid4()),
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "hashed_password": "$2b$12$test_hash_that_is_long_enough_for_bcrypt",
        }
        return {**defaults, **kwargs}

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Alias for build."""
        return cls.build(**kwargs)

    @classmethod
    async def create_async(
        cls,
        db: AsyncSession,
        commit: bool = True,
        **kwargs: Any,
    ) -> User:
        """
        Create a User directly in the database.

        Args:
            db: Database session
            commit: Whether to commit the transaction
            **kwargs: Override default values

        Returns:
            User model instance
        """
        from app.user.user_model import User
        from app.user.user_service import hash_password

        data = cls.build(**kwargs)
        user = User(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            hashed_password=kwargs.get(
                "hashed_password", hash_password("TestPass123!")
            ),
        )
        db.add(user)
        if commit:
            await db.commit()
            await db.refresh(user)
        # Type narrowing: guarantees non-optional IDs for persisted entities
        assert user.user_id is not None
        return user


class UserCreateRequestFactory:
    """Factory for creating UserCreateRequest schema data."""

    @staticmethod
    def build(**kwargs: Any) -> dict[str, Any]:
        """
        Build user creation request data.

        Args:
            **kwargs: Override default values

        Returns:
            Dictionary with user creation data
        """
        defaults = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPass123!",
        }
        return {**defaults, **kwargs}

    @classmethod
    def create(cls, **kwargs: Any) -> UserCreateRequest:
        """Create a UserCreateRequest instance."""
        data = cls.build(**kwargs)
        return UserCreateRequest(**data)

    @classmethod
    def with_weak_password(cls, **kwargs: Any) -> UserCreateRequest:
        """Create a request with a weak password."""
        data = cls.build(password="weak", **kwargs)
        return UserCreateRequest(**data)

    @classmethod
    def with_invalid_email(cls, **kwargs: Any) -> UserCreateRequest:
        """Create a request with an invalid email."""
        data = cls.build(email="not-an-email", **kwargs)
        return UserCreateRequest(**data)


class UserLoginRequestFactory:
    """Factory for creating login request data."""

    @staticmethod
    def build(**kwargs: Any) -> dict[str, Any]:
        """Build login request data."""
        defaults = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "password": "TestPass123!",
        }
        return {**defaults, **kwargs}

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, str]:
        """Create login request dictionary."""
        return cls.build(**kwargs)


# =============================================================================
# Todo Factories
# =============================================================================
class TodoFactory:
    """Factory for creating Todo model data."""

    @staticmethod
    def build(user_id: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """
        Build todo data dictionary.

        Args:
            user_id: User ID to associate todo with (optional)
            **kwargs: Override default values

        Returns:
            Dictionary with todo data
        """
        defaults = {
            "todo_id": str(uuid.uuid4()),
            "user_id": user_id or str(uuid.uuid4()),
            "title": f"Test Todo {uuid.uuid4().hex[:6]}",
            "description": "Test description",
            "completed": False,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        return {**defaults, **kwargs}

    @classmethod
    def create(cls, user_id: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Alias for build."""
        return cls.build(user_id, **kwargs)

    @classmethod
    def create_batch(
        cls, user_id: str, count: int = 3, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Create multiple todos for a user."""
        return [cls.build(user_id=user_id, **kwargs) for _ in range(count)]

    @classmethod
    async def create_async(
        cls,
        db: AsyncSession,
        user_id: str | None = None,
        commit: bool = True,
        **kwargs: Any,
    ) -> Todo:
        """
        Create a Todo directly in the database.

        Args:
            db: Database session
            user_id: User ID to associate todo with
            commit: Whether to commit the transaction
            **kwargs: Override default values

        Returns:
            Todo model instance
        """
        from app.todo.todo_model import Todo

        data = cls.build(user_id=user_id, **kwargs)
        todo = Todo(
            todo_id=data["todo_id"],
            user_id=data["user_id"],
            title=data["title"],
            description=data["description"],
            completed=data["completed"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
        db.add(todo)
        if commit:
            await db.commit()
            await db.refresh(todo)
        # Type narrowing: guarantees non-optional IDs for persisted entities
        assert todo.user_id is not None
        return todo

    @classmethod
    async def create_batch_async(
        cls,
        db: AsyncSession,
        user_id: str,
        count: int = 3,
        commit: bool = True,
        **kwargs: Any,
    ) -> list[Todo]:
        """
        Create multiple Todos directly in the database.

        Args:
            db: Database session
            user_id: User ID to associate todos with
            count: Number of todos to create
            commit: Whether to commit the transaction
            **kwargs: Override default values

        Returns:
            List of Todo model instances
        """
        from app.todo.todo_model import Todo

        todos_data = cls.create_batch(user_id=user_id, count=count, **kwargs)
        todos = []
        for data in todos_data:
            todo = Todo(
                todo_id=data["todo_id"],
                user_id=data["user_id"],
                title=data["title"],
                description=data["description"],
                completed=data["completed"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
            db.add(todo)
            todos.append(todo)
        if commit:
            await db.commit()
            for todo in todos:
                await db.refresh(todo)
        # Type narrowing: guarantees non-optional IDs for persisted entities
        for todo in todos:
            assert todo.user_id is not None
        return todos


class TodoCreateRequestFactory:
    """Factory for creating TodoCreate schema data."""

    @staticmethod
    def build(**kwargs: Any) -> dict[str, Any]:
        """Build todo creation request data."""
        defaults = {
            "title": f"Test Todo {uuid.uuid4().hex[:6]}",
            "description": "Test description for the todo",
        }
        return {**defaults, **kwargs}

    @classmethod
    def create(cls, **kwargs: Any) -> TodoCreate:
        """Create a TodoCreate instance."""
        data = cls.build(**kwargs)
        return TodoCreate(**data)

    @classmethod
    def with_long_title(cls, **kwargs: Any) -> TodoCreate:
        """Create a request with a very long title."""
        data = cls.build(title="A" * 201, **kwargs)
        return TodoCreate(**data)

    @classmethod
    def with_empty_title(cls, **kwargs: Any) -> TodoCreate:
        """Create a request with empty title."""
        data = cls.build(title="", **kwargs)
        return TodoCreate(**data)


class TodoUpdateRequestFactory:
    """Factory for creating TodoUpdate schema data."""

    @staticmethod
    def build(**kwargs: Any) -> dict[str, Any]:
        """Build todo update request data."""
        defaults = {
            "title": f"Updated Todo {uuid.uuid4().hex[:6]}",
            "description": "Updated description",
            "completed": True,
        }
        return {**defaults, **kwargs}

    @classmethod
    def create(cls, **kwargs: Any) -> TodoUpdate:
        """Create a TodoUpdate instance."""
        data = cls.build(**kwargs)
        return TodoUpdate(**data)

    @classmethod
    def create_completed(cls, **kwargs: Any) -> TodoUpdate:
        """Create an update to mark todo as completed."""
        data = cls.build(completed=True, **kwargs)
        return TodoUpdate(**data)

    @classmethod
    def create_partial(cls, **kwargs: Any) -> TodoUpdate:
        """Create a partial update (only some fields)."""
        data = {k: v for k, v in kwargs.items() if v is not None}
        return TodoUpdate(**data) if data else TodoUpdate()


# =============================================================================
# Token Factories
# =============================================================================
class TokenFactory:
    """Factory for creating authentication tokens."""

    @staticmethod
    def create_access_token(
        user_id: str | None = None,
        expires_delta: int | None = None,
    ) -> str:
        """Create a valid JWT access token."""
        from datetime import timedelta

        from app.user.user_auth import create_access_token

        user_id = user_id or str(uuid.uuid4())
        expires_delta = expires_delta or 1800  # 30 minutes

        return create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=expires_delta),
        )

    @staticmethod
    def create_expired_token(user_id: str | None = None) -> str:
        """Create an expired JWT token."""
        from datetime import timedelta

        from app.user.user_auth import create_access_token

        user_id = user_id or str(uuid.uuid4())

        return create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(seconds=-1),
        )

    @staticmethod
    def create_invalid_token() -> str:
        """Create an invalid JWT token."""
        return "invalid.token.string"

    @classmethod
    async def create_for_user(cls, db: AsyncSession, **kwargs: Any) -> tuple[User, str]:
        """
        Create a user in DB and generate a token for them.

        Args:
            db: Database session
            **kwargs: Override user default values

        Returns:
            Tuple of (User, token_string)
        """

        user = await UserFactory.create_async(db=db, **kwargs)
        # Type narrowing: user_id is guaranteed non-optional after creation
        assert user.user_id is not None
        token = cls.create_access_token(user_id=user.user_id)
        return user, token

    @classmethod
    async def create_user_and_headers(
        cls, db: AsyncSession
    ) -> tuple[User, dict[str, str]]:
        """
        Create a user in DB and return user with auth headers.

        Args:
            db: Database session

        Returns:
            Tuple of (User, auth_headers_dict)
        """
        user, token = await cls.create_for_user(db)
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers


# =============================================================================
# Response Factories
# =============================================================================
class ResponseFactory:
    """Factory for creating expected API responses."""

    @staticmethod
    def success_response(message: str, data: Any = None) -> dict[str, Any]:
        """Create a success response."""
        response = {
            "status": "success",
            "message": message,
        }
        if data is not None:
            response["data"] = data
        return response

    @staticmethod
    def error_response(message: str, errors: Any = None) -> dict[str, Any]:
        """Create an error response."""
        response = {
            "status": "error",
            "message": message,
        }
        if errors is not None:
            response["errors"] = errors
        return response

    @staticmethod
    def paginated_response(
        data: list[Any],
        total_size: int,
        page_number: int,
        page_size: int,
    ) -> dict[str, Any]:
        """Create a paginated response."""
        total_pages = (total_size + page_size - 1) // page_size if total_size else 0
        return {
            "status": "success",
            "message": "Todos retrieved successfully",
            "data": data,
            "total_size": total_size,
            "page_number": page_number,
            "page_size": page_size,
            "total_pages": total_pages,
        }
