#!/bin/bash

# FastAPI Demo Setup Script
# This script sets up the entire project in one command
# It is idempotent - safe to run multiple times

set -e  # Exit on any error

echo "========================================"
echo "FastAPI Demo - Project Setup"
echo "========================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed."
    echo "Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Or visit: https://github.com/astral-sh/uv"
    exit 1
fi

echo "✓ uv is installed"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
uv sync
echo "✓ Dependencies installed"
echo ""

# Setup environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
else
    echo "ℹ️  .env file already exists, skipping..."
fi
echo ""

# Initialize database with Alembic
echo "🗄️  Setting up database..."

# Check if any migration files exist
MIGRATION_COUNT=$(find alembic/versions -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l | tr -d ' ')

if [ "$MIGRATION_COUNT" -eq "0" ]; then
    echo "📝 No migrations found. Creating initial migration..."
    uv run alembic revision --autogenerate -m "Initial migration"
    echo "✓ Initial migration created"
else
    echo "✓ Found $MIGRATION_COUNT existing migration(s)"
fi

# Apply migrations
if [ ! -f app.db ]; then
    echo "🔨 Creating database and applying migrations..."
    uv run alembic upgrade head
    echo "✓ Database created and initialized"
else
    echo "🔄 Database exists. Checking for pending migrations..."
    # Get current and head revisions (compatible with macOS and Linux)
    CURRENT=$(uv run alembic current 2>/dev/null | grep -o '([a-f0-9]*)' | tr -d '()' || echo "none")
    HEAD=$(uv run alembic heads 2>/dev/null | grep -o '^[a-f0-9]*' | head -1 || echo "none")

    if [ "$CURRENT" = "$HEAD" ] && [ "$CURRENT" != "none" ]; then
        echo "✓ Database is up to date"
    else
        echo "📝 Applying pending migrations..."
        uv run alembic upgrade head
        echo "✓ Migrations applied"
    fi
fi
echo ""

# Verify database schema
echo "🔍 Verifying database schema..."
if sqlite3 app.db "SELECT name FROM sqlite_master WHERE type='table' AND name='users';" | grep -q "users"; then
    echo "✓ Users table exists"
    USER_COUNT=$(sqlite3 app.db "SELECT COUNT(*) FROM users;")
    echo "ℹ️  Database contains $USER_COUNT user(s)"
else
    echo "⚠️  Warning: Users table not found in database"
fi
echo ""

# Run a quick health check
echo "🏥 Running health check..."
if uv run python -c "from app.main import app; from app.core.database import engine; engine.connect()" 2>/dev/null; then
    echo "✓ Application can connect to database"
else
    echo "⚠️  Warning: Could not verify database connection"
fi
echo ""

# Seed the database with sample data
echo "🌱 Seeding database with sample data..."
if uv run python seed_db.py; then
    echo "✓ Database seeding complete"
else
    echo "⚠️  Warning: Database seeding had issues (this may be OK if data already exists)"
fi
echo ""

echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""

# Run verification
echo "🔍 Running setup verification..."
echo ""
if bash test_setup.sh; then
    echo ""
    echo "========================================"
    echo "🎉 Success! Everything is ready!"
    echo "========================================"
    echo ""
    echo "📋 What's ready:"
    echo "   • Python dependencies installed"
    echo "   • Environment variables configured (.env)"
    echo "   • Database created and migrated (app.db)"
    echo "   • Sample data seeded (3 demo users)"
    echo "   • API application ready to run"
    echo ""
    echo "🚀 To start the development server:"
    echo ""
    echo "   make dev"
    echo ""
    echo "   Or manually:"
    echo "   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    echo "📚 Once running, visit:"
    echo "   • http://localhost:8000/          - API root"
    echo "   • http://localhost:8000/docs      - Interactive API docs (Swagger UI)"
    echo "   • http://localhost:8000/redoc     - Alternative API docs (ReDoc)"
    echo "   • http://localhost:8000/health    - Health check"
    echo ""
    echo "🧪 Other useful commands:"
    echo "   make test          - Run all tests"
    echo "   make verify        - Verify setup again"
    echo "   make help          - Show all available commands"
    echo ""
    echo "📖 For more information:"
    echo "   • README.md         - Full documentation"
    echo "   • QUICK_START.md    - Quick start guide"
    echo "   • DEVELOPMENT.md    - Development guide"
    echo ""
else
    echo ""
    echo "⚠️  Setup completed but verification found some issues."
    echo "Please review the output above and try running 'bash setup.sh' again."
    echo ""
fi
