#!/bin/bash

# Test Setup Script
# Verifies that the FastAPI Demo project is correctly set up

echo "========================================"
echo "FastAPI Demo - Setup Verification"
echo "========================================"
echo ""

FAILED=0
PASSED=0

# Helper functions
check_pass() {
    echo "✓ $1"
    ((PASSED++))
}

check_fail() {
    echo "❌ $1"
    ((FAILED++))
}

# Test 1: Check if uv is installed
echo "🔍 Checking prerequisites..."
if command -v uv &> /dev/null; then
    check_pass "uv is installed"
else
    check_fail "uv is not installed"
fi
echo ""

# Test 2: Check if virtual environment exists
echo "🔍 Checking Python environment..."
if [ -d ".venv" ]; then
    check_pass "Virtual environment exists"
else
    check_fail "Virtual environment not found"
fi
echo ""

# Test 3: Check if .env file exists
echo "🔍 Checking configuration files..."
if [ -f ".env" ]; then
    check_pass ".env file exists"
else
    check_fail ".env file not found"
fi

if [ -f "pyproject.toml" ]; then
    check_pass "pyproject.toml exists"
else
    check_fail "pyproject.toml not found"
fi

if [ -f "alembic.ini" ]; then
    check_pass "alembic.ini exists"
else
    check_fail "alembic.ini not found"
fi
echo ""

# Test 4: Check if database exists
echo "🔍 Checking database..."
if [ -f "app.db" ]; then
    check_pass "Database file exists (app.db)"

    # Check if users table exists
    if sqlite3 app.db "SELECT name FROM sqlite_master WHERE type='table' AND name='users';" | grep -q "users"; then
        check_pass "Users table exists"

        # Check user count
        USER_COUNT=$(sqlite3 app.db "SELECT COUNT(*) FROM users;")
        if [ "$USER_COUNT" -gt 0 ]; then
            check_pass "Database contains $USER_COUNT user(s)"
        else
            check_fail "Database is empty (no users found)"
        fi

        # Check if demo user exists
        if sqlite3 app.db "SELECT email FROM users WHERE email='demo@fastapi-demo.com';" | grep -q "demo@fastapi-demo.com"; then
            check_pass "Demo user exists in database"
        else
            check_fail "Demo user not found in database"
        fi
    else
        check_fail "Users table not found"
    fi
else
    check_fail "Database file not found"
fi
echo ""

# Test 5: Check if migrations exist
echo "🔍 Checking database migrations..."
MIGRATION_COUNT=$(find alembic/versions -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l | tr -d ' ')
if [ "$MIGRATION_COUNT" -gt 0 ]; then
    check_pass "Found $MIGRATION_COUNT migration file(s)"
else
    check_fail "No migration files found"
fi
echo ""

# Test 6: Test Python imports
echo "🔍 Testing Python application..."
if uv run python -c "from app.main import app" 2>/dev/null; then
    check_pass "Can import FastAPI application"
else
    check_fail "Cannot import FastAPI application"
fi

if uv run python -c "from app.core.database import engine; engine.connect()" 2>/dev/null; then
    check_pass "Can connect to database"
else
    check_fail "Cannot connect to database"
fi

if uv run python -c "from app.models.user import User; from app.schemas.user import UserCreate" 2>/dev/null; then
    check_pass "Can import models and schemas"
else
    check_fail "Cannot import models and schemas"
fi
echo ""

# Test 7: Verify critical files exist
echo "🔍 Checking application structure..."
REQUIRED_FILES=(
    "app/main.py"
    "app/core/config.py"
    "app/core/database.py"
    "app/models/user.py"
    "app/schemas/user.py"
    "app/crud/user.py"
    "app/api/users.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "Found $file"
    else
        check_fail "Missing $file"
    fi
done
echo ""

# Test 8: Quick API health check (if server is not running)
echo "🔍 Testing API endpoints..."
# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "ℹ️  Server is already running, testing endpoints..."

    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        check_pass "Health endpoint responding"
    else
        check_fail "Health endpoint not responding correctly"
    fi

    if curl -s http://localhost:8000/ | grep -q "message"; then
        check_pass "Root endpoint responding"
    else
        check_fail "Root endpoint not responding correctly"
    fi
else
    echo "ℹ️  Server not running (this is OK - run 'make dev' to start it)"
fi
echo ""

# Test 9: Verify test suite
echo "🔍 Checking test suite..."
if [ -d "tests" ]; then
    check_pass "Tests directory exists"

    TEST_FILE_COUNT=$(find tests -name "test_*.py" | wc -l | tr -d ' ')
    if [ "$TEST_FILE_COUNT" -gt 0 ]; then
        check_pass "Found $TEST_FILE_COUNT test file(s)"
    else
        check_fail "No test files found"
    fi
else
    check_fail "Tests directory not found"
fi
echo ""

# Test 10: Verify documentation
echo "🔍 Checking documentation..."
DOC_FILES=("README.md" "QUICK_START.md" "DEVELOPMENT.md")
for doc in "${DOC_FILES[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "$doc exists"
    else
        check_fail "$doc not found"
    fi
done
echo ""

# Summary
echo "========================================"
echo "📊 Verification Summary"
echo "========================================"
echo ""
echo "✓ Passed: $PASSED"
if [ $FAILED -gt 0 ]; then
    echo "❌ Failed: $FAILED"
else
    echo "❌ Failed: 0"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All checks passed!"
    echo ""
    echo "Your FastAPI Demo project is correctly set up and ready to use!"
    echo ""
    echo "Next steps:"
    echo "  1. Start the server:    make dev"
    echo "  2. Run tests:           make test"
    echo "  3. View API docs:       http://localhost:8000/docs"
    echo ""
    exit 0
else
    echo "⚠️  Some checks failed!"
    echo ""
    echo "Please run the setup script to fix any issues:"
    echo "  bash setup.sh"
    echo ""
    exit 1
fi
