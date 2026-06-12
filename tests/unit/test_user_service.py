"""
Unit tests for user service functionality.

Tests cover:
- User registration
- User login
- Password hashing
- User validation
"""

import pytest

from app.core.auth import create_refresh_token, is_token_blacklisted
from app.core.exceptions import InvalidCredentialsError
from app.schemas.user_schema import UserCreateRequest
from app.services.user_service import (
    hash_password,
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
    verify_password,
)
from tests.factories import TokenFactory, UserFactory


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
        from app.core.exceptions import UserAlreadyExistsError

        await UserFactory.create_async(
            db=test_db,
            username="existinguser",
            email="existing@example.com",
        )

        user_data = UserCreateRequest(
            username="existinguser",
            email="different@example.com",
            password="SecurePass123!",
        )

        with pytest.raises(UserAlreadyExistsError):
            await register_user(test_db, user_data)

    async def test_register_user_duplicate_email(self, test_db):
        """Test registration with duplicate email."""
        from app.core.exceptions import UserAlreadyExistsError

        await UserFactory.create_async(
            db=test_db,
            username="existinguser",
            email="existing@example.com",
        )

        user_data = UserCreateRequest(
            username="differentuser",
            email="existing@example.com",
            password="SecurePass123!",
        )

        with pytest.raises(UserAlreadyExistsError):
            await register_user(test_db, user_data)

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

        from app.core.exceptions import UserAlreadyExistsError

        with pytest.raises(UserAlreadyExistsError):
            await register_user(test_db, user_data)

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
        from app.crud.user_crud import get_user_by_username

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
        from app.core.exceptions import InvalidCredentialsError

        await UserFactory.create_async(
            db=test_db,
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("correctpassword"),
        )

        with pytest.raises(InvalidCredentialsError):
            await login_user(test_db, "testuser", "wrongpassword")

    async def test_login_user_nonexistent_username(self, test_db):
        """Test login with non-existent username."""
        from app.core.exceptions import InvalidCredentialsError

        with pytest.raises(InvalidCredentialsError):
            await login_user(test_db, "nonexistent", "somepassword")


@pytest.mark.unit
class TestPasswordValidation:
    """Tests for password validation in schema."""

    def test_password_minimum_length(self):
        """Test password must be at least 8 characters."""
        from pydantic import ValidationError

        from app.schemas.user_schema import UserCreateRequest

        with pytest.raises(ValidationError):
            UserCreateRequest(
                username="testuser", email="test@example.com", password="short"
            )

    def test_password_maximum_length(self):
        """Test password must not exceed 128 characters."""
        from pydantic import ValidationError

        from app.schemas.user_schema import UserCreateRequest

        with pytest.raises(ValidationError):
            UserCreateRequest(
                username="testuser", email="test@example.com", password="A" * 129
            )

    def test_valid_password(self):
        """Test valid password passes validation."""
        from app.schemas.user_schema import UserCreateRequest

        user = UserCreateRequest(
            username="testuser", email="test@example.com", password="ValidPass123!"
        )

        assert user.password == "ValidPass123!"


@pytest.mark.unit
class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email passes validation."""
        from app.schemas.user_schema import UserCreateRequest

        user = UserCreateRequest(
            username="testuser", email="test@example.com", password="ValidPass123!"
        )

        assert user.email == "test@example.com"

    def test_invalid_email(self):
        """Test invalid email fails validation."""
        from pydantic import ValidationError

        from app.schemas.user_schema import UserCreateRequest

        with pytest.raises(ValidationError):
            UserCreateRequest(
                username="testuser", email="not-an-email", password="ValidPass123!"
            )


@pytest.mark.unit
class TestRefreshTokens:
    """Tests for refresh_tokens rotation and revocation."""

    async def test_refresh_issues_new_pair(self, test_db, fake_redis):
        """A valid refresh token yields a fresh access/refresh pair."""
        user = await UserFactory.create_async(db=test_db)
        old_refresh = create_refresh_token({"sub": user.user_id})

        tokens = await refresh_tokens(test_db, fake_redis, old_refresh)

        assert tokens.access_token
        assert tokens.refresh_token != old_refresh

    async def test_refresh_blacklists_old_token(self, test_db, fake_redis):
        """Rotation blacklists the old token so it cannot be reused."""
        user = await UserFactory.create_async(db=test_db)
        old_refresh = create_refresh_token({"sub": user.user_id})

        await refresh_tokens(test_db, fake_redis, old_refresh)

        with pytest.raises(InvalidCredentialsError):
            await refresh_tokens(test_db, fake_redis, old_refresh)

    async def test_refresh_invalid_token(self, test_db, fake_redis):
        """An unparseable refresh token is rejected."""
        with pytest.raises(InvalidCredentialsError):
            await refresh_tokens(test_db, fake_redis, "not.a.token")

    async def test_refresh_unknown_user(self, test_db, fake_redis):
        """A refresh token for a non-existent user is rejected."""
        ghost_refresh = create_refresh_token({"sub": "missing-user-id"})

        with pytest.raises(InvalidCredentialsError):
            await refresh_tokens(test_db, fake_redis, ghost_refresh)


@pytest.mark.unit
class TestLogoutUser:
    """Tests for logout_user token blacklisting."""

    async def test_logout_blacklists_access_token(self, test_db, fake_redis):
        """Logout adds the access token's JTI to the blacklist."""
        from app.core.auth import decode_access_token

        _, token = await TokenFactory.create_for_user(test_db)

        await logout_user(fake_redis, token)

        payload = decode_access_token(token)
        assert payload is not None
        assert await is_token_blacklisted(fake_redis, payload["jti"]) is True
