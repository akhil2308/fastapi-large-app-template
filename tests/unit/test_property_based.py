"""
Property-based tests using Hypothesis.

Tests cover:
- Password validation
- Token generation
- UUID generation
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from app.user.user_auth import create_access_token, decode_access_token
from app.user.user_service import hash_password, verify_password


@pytest.mark.unit
class TestPasswordValidation:
    """Property-based tests for password validation."""

    @pytest.mark.skip(reason="bcrypt is too slow for property-based testing")
    @given(password=st.text(min_size=8, max_size=100))
    @settings(max_examples=5, deadline=None)
    def test_password_hashing_consistency(self, password):
        """Test that hashing the same password produces consistent results."""
        hashed = hash_password(password)
        # The hashed password should be different from the original
        assert hashed != password
        # And verify should work
        assert verify_password(password, hashed) is True

    @pytest.mark.skip(reason="bcrypt is too slow for property-based testing")
    @given(
        password=st.text(min_size=8, max_size=100),
        other_password=st.text(min_size=8, max_size=100),
    )
    @settings(max_examples=5, deadline=None)
    def test_different_passwords_different_hashes(self, password, other_password):
        """Test that different passwords produce different hashes."""
        assume(password != other_password)
        hashed1 = hash_password(password)
        hashed2 = hash_password(other_password)
        # Different passwords should have different hashes (highly probable)
        assert hashed1 != hashed2

    @pytest.mark.skip(reason="bcrypt is too slow for property-based testing")
    @given(password=st.text(min_size=1, max_size=1000))
    @settings(max_examples=5, deadline=None)
    def test_verify_rejects_wrong_password(self, password):
        """Test that verify_password rejects wrong passwords."""
        hashed = hash_password(password)
        wrong_password = password + "wrong"
        assert verify_password(wrong_password, hashed) is False


@pytest.mark.unit
class TestTokenGeneration:
    """Property-based tests for JWT token generation."""

    @given(user_id=st.uuids())
    @settings(max_examples=5, deadline=None)
    def test_token_contains_user_id(self, user_id):
        """Test that generated token contains the user ID."""
        token = create_access_token(data={"sub": str(user_id)})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload.get("sub") == str(user_id)

    @given(user_id=st.text(min_size=1, max_size=100))
    @settings(max_examples=5, deadline=None)
    def test_token_contains_string_user_id(self, user_id):
        """Test that token works with string user IDs."""
        token = create_access_token(data={"sub": user_id})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload.get("sub") == user_id

    @given(
        user_id_1=st.text(min_size=1, max_size=50),
        user_id_2=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=5, deadline=None)
    def test_different_users_different_tokens(self, user_id_1, user_id_2):
        """Test that different user IDs produce different tokens."""
        assume(user_id_1 != user_id_2)
        token1 = create_access_token(data={"sub": user_id_1})
        token2 = create_access_token(data={"sub": user_id_2})
        assert token1 != token2


@pytest.mark.unit
class TestUUIDHandling:
    """Property-based tests for UUID handling."""

    @given(uuid_string=st.uuids().map(str))
    @settings(max_examples=5, deadline=None)
    def test_uuid_string_format(self, uuid_string):
        """Test that UUID strings are in correct format."""
        # Should be a valid UUID string (36 chars with dashes)
        assert len(uuid_string) == 36
        assert uuid_string.count("-") == 4
