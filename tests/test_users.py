"""
Example test file for the Users API.

To run tests: make test or uv run pytest
"""


def test_read_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_user(client, sample_user_data):
    """Test creating a new user."""
    response = client.post("/users/", json=sample_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == sample_user_data["email"]
    assert data["username"] == sample_user_data["username"]
    assert data["full_name"] == sample_user_data["full_name"]
    assert "id" in data
    assert data["is_active"] is True


def test_create_duplicate_email(client):
    """Test that duplicate emails are rejected."""
    # Create first user
    client.post(
        "/users/",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "full_name": "User One"
        }
    )

    # Try to create second user with same email
    response = client.post(
        "/users/",
        json={
            "email": "duplicate@example.com",
            "username": "user2",
            "full_name": "User Two"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_get_users(client):
    """Test getting list of users."""
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_user(client):
    """Test getting a specific user."""
    # Create a user first
    create_response = client.post(
        "/users/",
        json={
            "email": "getuser@example.com",
            "username": "getuser",
            "full_name": "Get User"
        }
    )
    user_id = create_response.json()["id"]

    # Get the user
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "getuser@example.com"


def test_get_nonexistent_user(client):
    """Test getting a user that doesn't exist."""
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_update_user(client):
    """Test updating a user."""
    # Create a user first
    create_response = client.post(
        "/users/",
        json={
            "email": "updateuser@example.com",
            "username": "updateuser",
            "full_name": "Update User"
        }
    )
    user_id = create_response.json()["id"]

    # Update the user
    response = client.patch(
        f"/users/{user_id}",
        json={"full_name": "Updated Name"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "updateuser@example.com"  # Email unchanged


def test_delete_user(client):
    """Test deleting a user."""
    # Create a user first
    create_response = client.post(
        "/users/",
        json={
            "email": "deleteuser@example.com",
            "username": "deleteuser",
            "full_name": "Delete User"
        }
    )
    user_id = create_response.json()["id"]

    # Delete the user
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 204

    # Verify user is deleted
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 404
