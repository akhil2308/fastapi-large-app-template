"""
Unit tests for todo service functionality.

Tests cover:
- Todo creation
- Todo retrieval with pagination
- Todo updates
- Soft delete
"""

import pytest

from app.todo.todo_schema import TodoCreate
from app.todo.todo_service import create_todo_service, get_todos_service
from tests.factories import TodoFactory, UserFactory


@pytest.mark.unit
class TestCreateTodoService:
    """Tests for create_todo_service function."""

    @pytest.mark.parametrize(
        "title,description,expected_description",
        [
            ("Test Todo", "Test Description", "Test Description"),
            ("Minimal", None, None),
            (
                "With HTML",
                "<script>alert('xss')</script>",
                "<script>alert('xss')</script>",
            ),
        ],
    )
    async def test_create_todo_various_inputs(
        self, test_db, title, description, expected_description
    ):
        """Test todo creation with various input combinations."""
        # Create a user first using factory
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )
        # Type narrowing: user_id is guaranteed non-optional
        assert user.user_id is not None

        # Create todo
        todo_data = TodoCreate(title=title, description=description)

        result = await create_todo_service(user.user_id, todo_data, test_db)

        assert result is not None
        assert result.title == title
        assert result.description == expected_description
        assert result.user_id == user.user_id
        assert result.completed is False

    async def test_create_todo_success(self, test_db):
        """Test successful todo creation."""
        # Create a user first using factory
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )
        # Type narrowing: user_id is guaranteed non-optional
        assert user.user_id is not None

        # Create todo
        todo_data = TodoCreate(title="Test Todo", description="Test Description")

        result = await create_todo_service(user.user_id, todo_data, test_db)

        assert result is not None
        assert result.title == "Test Todo"
        assert result.description == "Test Description"
        assert result.user_id == user.user_id
        assert result.completed is False

    async def test_create_todo_with_minimal_data(self, test_db):
        """Test todo creation with only required fields."""
        # Create a user first using factory
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
        )
        # Type narrowing: user_id is guaranteed non-optional
        assert user.user_id is not None

        # Create todo with only title
        todo_data = TodoCreate(title="Simple Todo")

        result = await create_todo_service(user.user_id, todo_data, test_db)

        assert result is not None
        assert result.title == "Simple Todo"
        assert result.description is None


@pytest.mark.unit
class TestGetTodosService:
    """Tests for get_todos_service function."""

    async def test_get_todos_success(self, test_db):
        """Test successful todo retrieval."""
        # Create a user with todos using factories
        user = await UserFactory.create_async(db=test_db)
        # Type narrowing: user_id is guaranteed non-optional
        assert user.user_id is not None

        # Add some todos
        await TodoFactory.create_batch_async(
            db=test_db,
            user_id=user.user_id,
            count=3,
        )

        # Get todos
        result = await get_todos_service(
            user.user_id, page_number=1, page_size=10, db=test_db
        )

        assert result is not None
        assert len(result["data"]) == 3
        assert result["total_size"] == 3
        assert result["page_number"] == 1
        assert result["page_size"] == 10

    async def test_get_todos_empty(self, test_db):
        """Test getting todos when user has none."""
        # Create a user but no todos
        user = await UserFactory.create_async(db=test_db)
        # Type narrowing: user_id is guaranteed non-optional
        assert user.user_id is not None

        result = await get_todos_service(
            user.user_id, page_number=1, page_size=10, db=test_db
        )

        assert result is not None
        assert len(result["data"]) == 0
        assert result["total_size"] is None or result["total_size"] == 0

    async def test_get_todos_pagination(self, test_db):
        """Test todo pagination."""
        # Create a user with many todos
        user = await UserFactory.create_async(db=test_db)
        # Type narrowing: user_id is guaranteed non-optional
        assert user.user_id is not None

        # Add 15 todos
        await TodoFactory.create_batch_async(
            db=test_db,
            user_id=user.user_id,
            count=15,
        )

        # Get first page
        result1 = await get_todos_service(
            user.user_id, page_number=1, page_size=5, db=test_db
        )
        assert len(result1["data"]) == 5
        assert result1["total_pages"] == 3

        # Get second page
        result2 = await get_todos_service(
            user.user_id, page_number=2, page_size=5, db=test_db
        )
        assert len(result2["data"]) == 5
        assert result2["page_number"] == 2

        # Get last page
        result3 = await get_todos_service(
            user.user_id, page_number=3, page_size=5, db=test_db
        )
        assert len(result3["data"]) == 5

    async def test_get_todos_excludes_deleted(self, test_db):
        """Test that soft-deleted todos are excluded."""
        # Create a user
        user = await UserFactory.create_async(db=test_db)
        # Type narrowing: user_id is guaranteed non-optional
        assert user.user_id is not None

        # Add active todo
        _active_todo = await TodoFactory.create_async(
            db=test_db,
            user_id=user.user_id,
            title="Active Todo",
        )

        # Add deleted todo
        deleted_todo = await TodoFactory.create_async(
            db=test_db,
            user_id=user.user_id,
            title="Deleted Todo",
            commit=False,
        )
        deleted_todo.is_deleted = True
        test_db.add(deleted_todo)
        await test_db.commit()

        # Get todos
        result = await get_todos_service(
            user.user_id, page_number=1, page_size=10, db=test_db
        )

        assert len(result["data"]) == 1
        assert result["data"][0].title == "Active Todo"


@pytest.mark.unit
class TestTodoSchema:
    """Tests for todo schema validation."""

    def test_todo_create_valid(self):
        """Test creating valid TodoCreate schema."""
        todo = TodoCreate(title="Test Todo", description="Test Description")

        assert todo.title == "Test Todo"
        assert todo.description == "Test Description"

    def test_todo_create_title_required(self):
        """Test that title is required."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TodoCreate.model_validate({"description": "No title"})

    def test_todo_create_title_length(self):
        """Test title length validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TodoCreate(title="")  # Empty title

    def test_todo_update_partial(self):
        """Test partial update with TodoUpdate."""
        from app.todo.todo_schema import TodoUpdate

        # Partial update - only title
        update = TodoUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.description is None
        assert update.completed is None

    def test_todo_update_complete(self):
        """Test complete update with TodoUpdate."""
        from app.todo.todo_schema import TodoUpdate

        update = TodoUpdate(
            title="New Title", description="New Description", completed=True
        )

        assert update.title == "New Title"
        assert update.description == "New Description"
        assert update.completed is True
