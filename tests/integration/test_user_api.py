"""
Integration tests for User API endpoints.

These tests verify that the API layer, CRUD operations, and database work together correctly.
"""
import pytest


class TestUserCreation:
    """Integration tests for user creation."""

    def test_create_user_success(self, client, sample_user_data):
        """Test successful user creation through API."""
        response = client.post("/users/", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert "id" in data
        assert data["is_active"] is True
        assert "created_at" in data

    def test_create_user_duplicate_email(self, client, sample_user_data):
        """Test that duplicate email is rejected."""
        # Create first user
        client.post("/users/", json=sample_user_data)

        # Try to create second user with same email
        duplicate_data = {
            "email": sample_user_data["email"],
            "username": "different_username",
            "full_name": "Different User"
        }
        response = client.post("/users/", json=duplicate_data)

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_create_user_duplicate_username(self, client, sample_user_data):
        """Test that duplicate username is rejected."""
        # Create first user
        client.post("/users/", json=sample_user_data)

        # Try to create second user with same username
        duplicate_data = {
            "email": "different@example.com",
            "username": sample_user_data["username"],
            "full_name": "Different User"
        }
        response = client.post("/users/", json=duplicate_data)

        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    def test_create_user_invalid_email(self, client):
        """Test creating user with invalid email."""
        invalid_data = {
            "email": "not-an-email",
            "username": "testuser",
            "full_name": "Test User"
        }
        response = client.post("/users/", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_create_user_missing_required_fields(self, client):
        """Test creating user with missing required fields."""
        incomplete_data = {
            "email": "test@example.com"
            # Missing username
        }
        response = client.post("/users/", json=incomplete_data)

        assert response.status_code == 422


class TestUserRetrieval:
    """Integration tests for retrieving users."""

    def test_get_users_empty(self, client):
        """Test getting users when there are none."""
        response = client.get("/users/")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_users(self, client):
        """Test getting list of users."""
        # Create multiple users
        for i in range(3):
            user_data = {
                "email": f"user{i}@example.com",
                "username": f"user{i}",
                "full_name": f"User {i}"
            }
            client.post("/users/", json=user_data)

        response = client.get("/users/")

        assert response.status_code == 200
        users = response.json()
        assert len(users) == 3

    def test_get_users_pagination(self, client):
        """Test pagination parameters."""
        # Create 5 users
        for i in range(5):
            user_data = {
                "email": f"user{i}@example.com",
                "username": f"user{i}"
            }
            client.post("/users/", json=user_data)

        # Get with pagination
        response = client.get("/users/?skip=2&limit=2")

        assert response.status_code == 200
        users = response.json()
        assert len(users) == 2

    def test_get_user_by_id(self, client, sample_user_data):
        """Test getting a specific user by ID."""
        # Create a user
        create_response = client.post("/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Get the user
        response = client.get(f"/users/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]

    def test_get_nonexistent_user(self, client):
        """Test getting a user that doesn't exist."""
        response = client.get("/users/99999")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestUserUpdate:
    """Integration tests for updating users."""

    def test_update_user_full_name(self, client, create_user):
        """Test updating user's full name."""
        # Create a user
        create_response = create_user()
        user_id = create_response.json()["id"]

        # Update the user
        update_data = {"full_name": "Updated Name"}
        response = client.patch(f"/users/{user_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert "updated_at" in data

    def test_update_user_multiple_fields(self, client, create_user):
        """Test updating multiple fields."""
        # Create a user
        create_response = create_user()
        user_id = create_response.json()["id"]

        # Update multiple fields
        update_data = {
            "full_name": "New Name",
            "is_active": False
        }
        response = client.patch(f"/users/{user_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "New Name"
        assert data["is_active"] is False

    def test_update_nonexistent_user(self, client):
        """Test updating a user that doesn't exist."""
        update_data = {"full_name": "New Name"}
        response = client.patch("/users/99999", json=update_data)

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_update_user_empty_payload(self, client, create_user):
        """Test update with empty payload (should succeed)."""
        # Create a user
        create_response = create_user()
        user_id = create_response.json()["id"]
        original_data = create_response.json()

        # Update with empty payload
        response = client.patch(f"/users/{user_id}", json={})

        assert response.status_code == 200
        # Data should remain unchanged
        data = response.json()
        assert data["email"] == original_data["email"]
        assert data["username"] == original_data["username"]


class TestUserDeletion:
    """Integration tests for deleting users."""

    def test_delete_user(self, client, create_user):
        """Test deleting a user."""
        # Create a user
        create_response = create_user()
        user_id = create_response.json()["id"]

        # Delete the user
        response = client.delete(f"/users/{user_id}")

        assert response.status_code == 204

        # Verify user is deleted
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_user(self, client):
        """Test deleting a user that doesn't exist."""
        response = client.delete("/users/99999")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_delete_user_idempotent(self, client, create_user):
        """Test that deleting a user twice returns 404 on second attempt."""
        # Create a user
        create_response = create_user()
        user_id = create_response.json()["id"]

        # Delete the user first time
        response1 = client.delete(f"/users/{user_id}")
        assert response1.status_code == 204

        # Try to delete again
        response2 = client.delete(f"/users/{user_id}")
        assert response2.status_code == 404


class TestUserWorkflows:
    """Integration tests for complete user workflows."""

    def test_create_update_get_delete_workflow(self, client, sample_user_data):
        """Test complete CRUD workflow."""
        # Create
        create_response = client.post("/users/", json=sample_user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        # Read
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email"] == sample_user_data["email"]

        # Update
        update_data = {"full_name": "Updated Name"}
        update_response = client.patch(f"/users/{user_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["full_name"] == "Updated Name"

        # Verify update
        get_response2 = client.get(f"/users/{user_id}")
        assert get_response2.json()["full_name"] == "Updated Name"

        # Delete
        delete_response = client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_response3 = client.get(f"/users/{user_id}")
        assert get_response3.status_code == 404

    def test_multiple_users_interaction(self, client):
        """Test creating and managing multiple users."""
        # Create multiple users
        user_ids = []
        for i in range(3):
            user_data = {
                "email": f"user{i}@example.com",
                "username": f"user{i}",
                "full_name": f"User {i}"
            }
            response = client.post("/users/", json=user_data)
            user_ids.append(response.json()["id"])

        # Verify all users exist
        list_response = client.get("/users/")
        assert len(list_response.json()) == 3

        # Update one user
        client.patch(
            f"/users/{user_ids[1]}",
            json={"full_name": "Modified User"}
        )

        # Delete one user
        client.delete(f"/users/{user_ids[0]}")

        # Verify final state
        list_response2 = client.get("/users/")
        users = list_response2.json()
        assert len(users) == 2

        # Check that the right user was modified
        modified_user = next(u for u in users if u["id"] == user_ids[1])
        assert modified_user["full_name"] == "Modified User"
