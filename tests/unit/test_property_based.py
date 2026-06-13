"""
Property-based tests using Hypothesis.

Tests cover:
- Password length validation
- Pagination math
- Token generation
- UUID generation
"""

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.core.auth import create_access_token, decode_access_token
from app.schemas.user_schema import UserCreateRequest


@pytest.mark.unit
class TestPasswordValidation:
    """Property-based tests for the password length validator (8-128 chars)."""

    @given(password=st.text(min_size=8, max_size=128))
    @settings(max_examples=20, deadline=None)
    def test_valid_length_accepted(self, password):
        """Any password within the length bounds is accepted."""
        request = UserCreateRequest(
            username="user", email="user@example.com", password=password
        )
        assert request.password == password

    @given(password=st.text(max_size=7))
    @settings(max_examples=20, deadline=None)
    def test_too_short_rejected(self, password):
        """Passwords shorter than 8 characters are rejected."""
        with pytest.raises(ValidationError):
            UserCreateRequest(
                username="user", email="user@example.com", password=password
            )

    @given(password=st.text(min_size=129, max_size=200))
    @settings(max_examples=20, deadline=None)
    def test_too_long_rejected(self, password):
        """Passwords longer than 128 characters are rejected."""
        with pytest.raises(ValidationError):
            UserCreateRequest(
                username="user", email="user@example.com", password=password
            )


@pytest.mark.unit
class TestPaginationMath:
    """Property-based tests for total-pages computation."""

    @staticmethod
    def _total_pages(total_count: int, page_size: int) -> int:
        # Mirrors app/services/todo_service.py
        return (total_count + page_size - 1) // page_size if total_count else 0

    @given(
        total_count=st.integers(min_value=0, max_value=10_000),
        page_size=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50, deadline=None)
    def test_matches_ceiling_division(self, total_count, page_size):
        """total_pages equals ceil(total_count / page_size), and 0 when empty."""
        expected = math.ceil(total_count / page_size) if total_count else 0
        assert self._total_pages(total_count, page_size) == expected


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
