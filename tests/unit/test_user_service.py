"""
Unit tests for user service functionality.

Tests cover:
- User registration
- User login
- Password hashing
- User validation
"""

import pytest

from app.user.user_schema import UserCreateRequest
from app.user.user_service import (
    hash_password,
    login_user,
    register_user,
    verify_password,
)
from tests.factories import UserFactory


@pytest.mark.unit
class TestRegisterUser:
    """Tests for register_user function."""

    async def test_register_user_success(self, test_db):
        """Test successful user registration."""
        user_data = UserCreateRequest(
            username="newuser", email="newuser@example.com", password="SecurePass123!"
        )

        result = await register_user(test_db, user_data)

        assert result is not None
        assert result.username == user_data.username
        assert result.email == user_data.email
        assert result.user_id is not None

    async def test_register_user_duplicate_username(self, test_db):
        """Test registration with duplicate username."""
        # Create existing user using factory
        await UserFactory.create_async(
            db=test_db,
            username="existinguser",
            email="existing@example.com",
        )

        # Try to register with same username
        user_data = UserCreateRequest(
            username="existinguser",
            email="different@example.com",
            password="SecurePass123!",
        )

        result = await register_user(test_db, user_data)

        assert result is None

    async def test_register_user_duplicate_email(self, test_db):
        """Test registration with duplicate email."""
        # Create existing user using factory
        await UserFactory.create_async(
            db=test_db,
            username="existinguser",
            email="existing@example.com",
        )

        # Try to register with same email
        user_data = UserCreateRequest(
            username="differentuser",
            email="existing@example.com",
            password="SecurePass123!",
        )

        result = await register_user(test_db, user_data)

        assert result is None

    @pytest.mark.parametrize(
        "duplicate_field,duplicate_value",
        [
            ("username", "existinguser"),
            ("email", "existing@example.com"),
        ],
    )
    async def test_register_user_duplicate_field(
        self, test_db, duplicate_field, duplicate_value
    ):
        """Test registration with duplicate username or email using parametrize."""
        # Create existing user using factory
        await UserFactory.create_async(
            db=test_db,
            username="existinguser",
            email="existing@example.com",
        )

        # Try to register with duplicate
        if duplicate_field == "username":
            user_data = UserCreateRequest(
                username=duplicate_value,
                email="new@example.com",
                password="SecurePass123!",
            )
        else:
            user_data = UserCreateRequest(
                username="newuser", email=duplicate_value, password="SecurePass123!"
            )

        result = await register_user(test_db, user_data)
        assert result is None

    async def test_register_user_hashes_password(self, test_db):
        """Test that password is properly hashed."""
        user_data = UserCreateRequest(
            username="newuser", email="newuser@example.com", password="SecurePass123!"
        )

        result = await register_user(test_db, user_data)

        assert result is not None
        # Verify user was created
        assert result.username == "newuser"

        # Verify password is hashed by checking the database model directly
        # The response schema doesn't expose hashed_password for security
        from app.user.user_crud import get_user_by_username

        user_model = await get_user_by_username(test_db, "newuser")
        assert user_model is not None
        # Type narrowing: hashed_password is guaranteed non-optional for persisted users
        assert user_model.hashed_password is not None
        # Verify password is hashed (not plaintext)
        assert user_model.hashed_password != user_data.password
        # Verify password can be verified
        assert verify_password(user_data.password, user_model.hashed_password) is True


@pytest.mark.unit
class TestLoginUser:
    """Tests for login_user function."""

    async def test_login_user_success(self, test_db):
        """Test successful user login."""
        # Create user with known password using factory
        password = "SecurePass123!"
        user = await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password(password),
        )

        # Login with correct credentials
        result = await login_user(test_db, "testuser", password)

        assert result is not None
        assert result.username == "testuser"
        assert result.user_id == user.user_id

    async def test_login_user_wrong_password(self, test_db):
        """Test login with wrong password."""
        # Create user using factory
        await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("correctpassword"),
        )

        # Login with wrong password
        result = await login_user(test_db, "testuser", "wrongpassword")

        assert result is None

    async def test_login_user_nonexistent_username(self, test_db):
        """Test login with non-existent username."""
        result = await login_user(test_db, "nonexistent", "somepassword")

        assert result is None


@pytest.mark.unit
class TestPasswordValidation:
    """Tests for password validation in schema."""

    def test_password_minimum_length(self):
        """Test password must be at least 8 characters."""
        from pydantic import ValidationError

        from app.user.user_schema import UserCreateRequest

        with pytest.raises(ValidationError):
            UserCreateRequest(
                username="testuser", email="test@example.com", password="short"
            )

    def test_password_maximum_length(self):
        """Test password must not exceed 128 characters."""
        from pydantic import ValidationError

        from app.user.user_schema import UserCreateRequest

        with pytest.raises(ValidationError):
            UserCreateRequest(
                username="testuser", email="test@example.com", password="A" * 129
            )

    def test_valid_password(self):
        """Test valid password passes validation."""
        from app.user.user_schema import UserCreateRequest

        user = UserCreateRequest(
            username="testuser", email="test@example.com", password="ValidPass123!"
        )

        assert user.password == "ValidPass123!"


@pytest.mark.unit
class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email passes validation."""
        from app.user.user_schema import UserCreateRequest

        user = UserCreateRequest(
            username="testuser", email="test@example.com", password="ValidPass123!"
        )

        assert user.email == "test@example.com"

    def test_invalid_email(self):
        """Test invalid email fails validation."""
        from pydantic import ValidationError

        from app.user.user_schema import UserCreateRequest

        with pytest.raises(ValidationError):
            UserCreateRequest(
                username="testuser", email="not-an-email", password="ValidPass123!"
            )
