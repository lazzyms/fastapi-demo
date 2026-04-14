"""
Unit tests for Pydantic schemas.

These tests verify that data validation works correctly.
"""

import pytest
from pydantic import ValidationError

from app.schemas.emails import PubSubMessage
from app.schemas.user import UserCreate, UserUpdate, UserResponse


class TestUserCreate:
    """Tests for UserCreate schema."""

    def test_valid_user_create(self):
        """Test creating a valid user schema."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
        }
        user = UserCreate(**data)
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"

    def test_user_create_without_full_name(self):
        """Test that full_name is optional."""
        data = {"email": "test@example.com", "username": "testuser"}
        user = UserCreate(**data)
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name is None

    def test_invalid_email(self):
        """Test that invalid email raises validation error."""
        data = {"email": "not-an-email", "username": "testuser"}
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        assert "email" in str(exc_info.value).lower()

    def test_missing_required_fields(self):
        """Test that missing required fields raises validation error."""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")  # Missing username

        with pytest.raises(ValidationError):
            UserCreate(username="testuser")  # Missing email


class TestUserUpdate:
    """Tests for UserUpdate schema."""

    def test_partial_update(self):
        """Test that all fields are optional in update schema."""
        # Should work with just one field
        user = UserUpdate(full_name="New Name")
        assert user.full_name == "New Name"
        assert user.email is None
        assert user.username is None

    def test_empty_update(self):
        """Test that update can be empty."""
        user = UserUpdate()
        assert user.email is None
        assert user.username is None
        assert user.full_name is None

    def test_update_multiple_fields(self):
        """Test updating multiple fields."""
        user = UserUpdate(email="new@example.com", full_name="New Name")
        assert user.email == "new@example.com"
        assert user.full_name == "New Name"


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_from_orm_model(self):
        """Test creating response from ORM model."""

        # Simulating an ORM object with attributes
        class MockUser:
            id = 1
            email = "test@example.com"
            username = "testuser"
            full_name = "Test User"
            is_active = True
            created_at = "2024-01-01T00:00:00"
            updated_at = None

        mock_user = MockUser()
        user = UserResponse.model_validate(mock_user)
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.username == "testuser"

    def test_model_dump(self):
        """Test converting schema to dict."""
        from datetime import datetime

        user = UserResponse(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            is_active=True,
            created_at=datetime(2024, 1, 1),
            updated_at=None,
        )
        data = user.model_dump()
        assert data["id"] == 1
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True


class TestPubSubMessage:
    """Tests for PubSubMessage schema aliases."""

    def test_accepts_google_pubsub_camel_case_fields(self):
        """Google push payloads use messageId/publishTime fields."""
        payload = {
            "messageId": "abc-123",
            "data": "eyJoaXN0b3J5SWQiOiIxIn0=",
            "publishTime": "2026-04-14T12:00:00Z",
        }

        message = PubSubMessage.model_validate(payload)

        assert message.message_id == "abc-123"
        assert message.publish_time == "2026-04-14T12:00:00Z"

    def test_accepts_snake_case_fields_for_internal_calls(self):
        """populate_by_name keeps internal snake_case compatibility."""
        payload = {
            "message_id": "abc-123",
            "data": "eyJoaXN0b3J5SWQiOiIxIn0=",
            "publish_time": "2026-04-14T12:00:00Z",
        }

        message = PubSubMessage.model_validate(payload)

        assert message.message_id == "abc-123"
        assert message.publish_time == "2026-04-14T12:00:00Z"
