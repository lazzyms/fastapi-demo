"""
Unit tests for CRUD operations.

These tests verify database operations in isolation.
"""
import pytest

from app.crud import user as crud_user
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


class TestCreateUser:
    """Tests for creating users."""

    def test_create_user(self, db_session):
        """Test creating a user."""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User"
        )
        user = crud_user.create_user(db_session, user_data)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.created_at is not None

    def test_create_user_without_full_name(self, db_session):
        """Test creating a user without full name."""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser"
        )
        user = crud_user.create_user(db_session, user_data)

        assert user.full_name is None
        assert user.email == "test@example.com"


class TestGetUser:
    """Tests for retrieving users."""

    def test_get_user_by_id(self, db_session):
        """Test getting a user by ID."""
        # Create a user first
        user_data = UserCreate(
            email="test@example.com",
            username="testuser"
        )
        created_user = crud_user.create_user(db_session, user_data)

        # Get the user
        user = crud_user.get_user(db_session, created_user.id)

        assert user is not None
        assert user.id == created_user.id
        assert user.email == "test@example.com"

    def test_get_nonexistent_user(self, db_session):
        """Test getting a user that doesn't exist."""
        user = crud_user.get_user(db_session, 99999)
        assert user is None

    def test_get_user_by_email(self, db_session):
        """Test getting a user by email."""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser"
        )
        crud_user.create_user(db_session, user_data)

        user = crud_user.get_user_by_email(db_session, "test@example.com")
        assert user is not None
        assert user.email == "test@example.com"

    def test_get_user_by_username(self, db_session):
        """Test getting a user by username."""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser"
        )
        crud_user.create_user(db_session, user_data)

        user = crud_user.get_user_by_username(db_session, "testuser")
        assert user is not None
        assert user.username == "testuser"


class TestGetUsers:
    """Tests for retrieving multiple users."""

    def test_get_users_empty(self, db_session):
        """Test getting users when there are none."""
        users = crud_user.get_users(db_session)
        assert len(users) == 0

    def test_get_users(self, db_session):
        """Test getting multiple users."""
        # Create multiple users
        for i in range(3):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                username=f"user{i}"
            )
            crud_user.create_user(db_session, user_data)

        users = crud_user.get_users(db_session)
        assert len(users) == 3

    def test_get_users_with_pagination(self, db_session):
        """Test pagination parameters."""
        # Create 5 users
        for i in range(5):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                username=f"user{i}"
            )
            crud_user.create_user(db_session, user_data)

        # Skip first 2, get next 2
        users = crud_user.get_users(db_session, skip=2, limit=2)
        assert len(users) == 2


class TestUpdateUser:
    """Tests for updating users."""

    def test_update_user(self, db_session):
        """Test updating a user."""
        # Create a user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User"
        )
        created_user = crud_user.create_user(db_session, user_data)

        # Update the user
        update_data = UserUpdate(full_name="Updated Name")
        updated_user = crud_user.update_user(
            db_session,
            created_user.id,
            update_data
        )

        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "test@example.com"  # Unchanged
        assert updated_user.updated_at is not None

    def test_update_nonexistent_user(self, db_session):
        """Test updating a user that doesn't exist."""
        update_data = UserUpdate(full_name="New Name")
        result = crud_user.update_user(db_session, 99999, update_data)
        assert result is None

    def test_partial_update(self, db_session):
        """Test updating only some fields."""
        # Create a user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User"
        )
        created_user = crud_user.create_user(db_session, user_data)

        # Update only email
        update_data = UserUpdate(email="new@example.com")
        updated_user = crud_user.update_user(
            db_session,
            created_user.id,
            update_data
        )

        assert updated_user.email == "new@example.com"
        assert updated_user.username == "testuser"  # Unchanged
        assert updated_user.full_name == "Test User"  # Unchanged


class TestDeleteUser:
    """Tests for deleting users."""

    def test_delete_user(self, db_session):
        """Test deleting a user."""
        # Create a user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser"
        )
        created_user = crud_user.create_user(db_session, user_data)

        # Delete the user
        result = crud_user.delete_user(db_session, created_user.id)
        assert result is True

        # Verify user is deleted
        user = crud_user.get_user(db_session, created_user.id)
        assert user is None

    def test_delete_nonexistent_user(self, db_session):
        """Test deleting a user that doesn't exist."""
        result = crud_user.delete_user(db_session, 99999)
        assert result is False
