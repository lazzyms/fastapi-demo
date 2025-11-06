# Test Suite Documentation

This directory contains comprehensive tests for the FastAPI Demo project.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests (isolated component tests)
│   ├── test_schemas.py      # Pydantic schema validation tests
│   └── test_crud.py         # Database operation tests
├── integration/             # Integration tests (API + database)
│   └── test_user_api.py     # User API endpoint tests
└── e2e/                     # End-to-end tests (complete scenarios)
    └── test_api_scenarios.py # Real-world usage scenarios
```

## Test Categories

### Unit Tests (`tests/unit/`)
Test individual components in isolation:
- **Schema tests**: Validate Pydantic models and data validation
- **CRUD tests**: Test database operations with an in-memory database

### Integration Tests (`tests/integration/`)
Test components working together:
- **API endpoint tests**: Test FastAPI routes with database
- **Request/Response validation**: Test API contracts
- **Error handling**: Test API error responses

### E2E Tests (`tests/e2e/`)
Test complete user scenarios:
- **User workflows**: Complete CRUD workflows
- **Business scenarios**: Team onboarding, profile updates
- **Edge cases**: Error handling, data consistency
- **Stub tests**: Placeholders for future features

## Running Tests

### Run All Tests
```bash
make test
# or
uv run pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# E2E tests only
uv run pytest tests/e2e/

# Run with markers
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m e2e
```

### Run Specific Test Files
```bash
uv run pytest tests/unit/test_schemas.py
uv run pytest tests/integration/test_user_api.py
```

### Run Specific Test Functions
```bash
uv run pytest tests/unit/test_schemas.py::TestUserCreate::test_valid_user_create
```

### Verbose Output
```bash
uv run pytest -v
uv run pytest -vv  # Extra verbose
```

### Show Print Statements
```bash
uv run pytest -s
```

### Stop on First Failure
```bash
uv run pytest -x
```

### Run Last Failed Tests
```bash
uv run pytest --lf
```

## Test Fixtures

### Available Fixtures (from `conftest.py`)

- **`db_session`**: Fresh in-memory database session for each test
- **`client`**: FastAPI TestClient with database override
- **`sample_user_data`**: Sample user data dictionary
- **`create_user`**: Helper function to create a user via API

### Using Fixtures

```python
def test_example(client, sample_user_data):
    response = client.post("/users/", json=sample_user_data)
    assert response.status_code == 201
```

## Writing New Tests

### Unit Test Example
```python
# tests/unit/test_new_feature.py
from app.schemas.user import UserCreate

def test_user_validation():
    user = UserCreate(email="test@example.com", username="test")
    assert user.email == "test@example.com"
```

### Integration Test Example
```python
# tests/integration/test_new_endpoint.py
def test_new_endpoint(client):
    response = client.get("/new-endpoint")
    assert response.status_code == 200
```

### E2E Test Example
```python
# tests/e2e/test_new_scenario.py
def test_complete_workflow(client):
    # Create
    create_resp = client.post("/users/", json={...})
    user_id = create_resp.json()["id"]

    # Update
    client.patch(f"/users/{user_id}", json={...})

    # Verify
    get_resp = client.get(f"/users/{user_id}")
    assert get_resp.status_code == 200
```

## Test Markers

Mark tests with categories:

```python
import pytest

@pytest.mark.unit
def test_unit_example():
    pass

@pytest.mark.integration
def test_integration_example():
    pass

@pytest.mark.e2e
def test_e2e_example():
    pass

@pytest.mark.slow
def test_slow_example():
    pass

@pytest.mark.skip(reason="Feature not implemented")
def test_future_feature():
    pass
```

Run tests by marker:
```bash
uv run pytest -m unit
uv run pytest -m "not slow"
```

## Coverage

To run tests with coverage (requires pytest-cov):

```bash
# Add to pyproject.toml first:
# dev-dependencies = [..., "pytest-cov>=6.0.0"]

# Then run:
uv sync
uv run pytest --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clear naming**: Test names should describe what they test
3. **Arrange-Act-Assert**: Structure tests in three parts
4. **Use fixtures**: Share common setup code
5. **Test edge cases**: Don't just test the happy path
6. **Keep tests fast**: Use in-memory database for speed
7. **Test one thing**: Each test should verify one behavior

## Example Test Structure

```python
def test_descriptive_name(client, db_session):
    # Arrange: Set up test data
    user_data = {"email": "test@example.com", "username": "test"}

    # Act: Perform the action
    response = client.post("/users/", json=user_data)

    # Assert: Verify the result
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]
```

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    uv sync
    uv run pytest -v
```

## Debugging Tests

### Run with Python debugger
```bash
uv run pytest --pdb  # Drop into debugger on failure
```

### Print variables
```python
def test_debug_example(client):
    response = client.get("/users/")
    print(f"Response: {response.json()}")  # Use -s flag to see prints
    assert response.status_code == 200
```

## Common Issues

### Database locked
- The in-memory database should prevent this
- If using file database, ensure proper cleanup

### Fixture not found
- Check that conftest.py is in the tests directory
- Ensure fixture name matches function parameter

### Import errors
- Run tests from project root directory
- Ensure app package is importable

## Adding Tests for New Features

When adding a new feature:

1. **Unit tests**: Test schemas and CRUD operations
2. **Integration tests**: Test API endpoints
3. **E2E tests**: Test complete user scenarios
4. **Update this README** if adding new test categories

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
