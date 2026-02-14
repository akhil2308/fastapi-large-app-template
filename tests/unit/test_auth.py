"""
Unit tests for authentication (JWT) functionality.

Tests cover:
- Token creation
- Token decoding
- Token expiration
- Invalid token handling
"""

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import patch

import pytest

from app.user.user_auth import create_access_token, decode_access_token
from app.user.user_model import User
from app.utils.auth_dependency import get_current_user


@pytest.mark.unit
class TestCreateAccessToken:
    """Tests for create_access_token function."""

    def test_create_token_with_default_expiry(self):
        """Test token creation with default expiration."""
        token = create_access_token(data={"sub": "test-user-id"})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_custom_expiry(self):
        """Test token creation with custom expiration."""
        custom_delta = timedelta(minutes=60)
        token = create_access_token(
            data={"sub": "test-user-id"}, expires_delta=custom_delta
        )

        assert token is not None
        assert isinstance(token, str)

    def test_create_token_includes_sub(self):
        """Test that token includes the subject claim."""
        user_id = "test-user-123"
        token = create_access_token(data={"sub": user_id})

        # Decode to verify payload
        payload = decode_access_token(token)
        assert payload is not None
        assert payload.get("sub") == user_id

    def test_create_token_includes_exp(self):
        """Test that token includes expiration claim."""
        token = create_access_token(data={"sub": "test-user-id"})

        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload

    def test_create_token_encodes_data(self):
        """Test that additional data is encoded in token."""
        data = {"sub": "test-user-id", "username": "testuser", "role": "admin"}
        token = create_access_token(data=data)

        payload = decode_access_token(token)
        assert payload is not None
        assert payload.get("sub") == "test-user-id"
        assert payload.get("username") == "testuser"
        assert payload.get("role") == "admin"


@pytest.mark.unit
class TestDecodeAccessToken:
    """Tests for decode_access_token function."""

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        # Create a valid token
        user_id = "test-user-123"
        token = create_access_token(data={"sub": user_id})

        # Decode it
        payload = decode_access_token(token)

        assert payload is not None
        assert payload.get("sub") == user_id

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        payload = decode_access_token("invalid.token.string")
        assert payload is None

    def test_decode_empty_token(self):
        """Test decoding an empty token."""
        payload = decode_access_token("")
        assert payload is None

    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        # Create a token that expires immediately

        # Manually create an expired token
        with patch("app.user.user_auth.datetime") as mock_datetime:
            # Set time to past
            mock_datetime.now.return_value = datetime(2020, 1, 1, tzinfo=UTC)
            mock_datetime.timedelta = timedelta

            token = create_access_token(
                data={"sub": "test-user"}, expires_delta=timedelta(seconds=-1)
            )

        # Try to decode it
        payload = decode_access_token(token)

        # JWT decode should fail for expired tokens
        # The function returns None on any PyJWTError
        assert payload is None

    def test_decode_token_missing_sub(self):
        """Test decoding a token without subject."""
        import jwt

        from app.core.settings import JWTConfig

        # Create token without 'sub' claim
        token = jwt.encode(
            {"some": "data"}, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM
        )

        payload = decode_access_token(token)
        assert payload is None or payload.get("sub") is None


@pytest.mark.unit
class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    async def test_get_current_user_valid_token(self, test_db):
        """Test getting current user with valid token."""
        # Create a test user
        user = User(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$hash",
        )
        test_db.add(user)
        await test_db.commit()

        # Create a valid token
        token = create_access_token(data={"sub": user.user_id})

        # Get current user
        result = await get_current_user(token=token, db=test_db)

        assert result is not None
        assert result.user_id == user.user_id
        assert result.username == user.username

    async def test_get_current_user_invalid_token(self, test_db):
        """Test getting current user with invalid token."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalid.token", db=test_db)

        assert exc_info.value.status_code == 401

    async def test_get_current_user_nonexistent_user(self, test_db):
        """Test getting current user that doesn't exist."""
        from fastapi import HTTPException

        # Create token for non-existent user
        token = create_access_token(data={"sub": "non-existent-id"})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=test_db)

        assert exc_info.value.status_code == 401

    async def test_get_current_user_no_token(self, test_db):
        """Test getting current user without token."""
        from fastapi import HTTPException

        # Create a mock OAuth2 scheme that raises
        async def raise_exception():
            raise HTTPException(status_code=401, detail="Not authenticated")

        with pytest.raises(HTTPException):
            # Use cast to explicitly pass None where str is expected
            # This test intentionally passes invalid data to trigger auth error
            await get_current_user(
                token=cast(str, None),  # Will cause OAuth2PasswordBearer to raise
                db=test_db,
            )


@pytest.mark.unit
class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        from app.user.user_service import hash_password

        hashed = hash_password("testpassword123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        from app.user.user_service import hash_password

        hash1 = hash_password("testpassword123")
        hash2 = hash_password("testpassword123")

        # Due to bcrypt salt, hashes should be different
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        from app.user.user_service import hash_password, verify_password

        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        from app.user.user_service import hash_password, verify_password

        hashed = hash_password("testpassword123")

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        """Test verifying empty password."""
        from app.user.user_service import hash_password, verify_password

        hashed = hash_password("testpassword123")

        assert verify_password("", hashed) is False
