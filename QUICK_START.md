# Quick Start Guide

Get up and running in 60 seconds!

## Prerequisites

Install [uv](https://github.com/astral-sh/uv):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

```bash
# Clone the repo
git clone <repository-url>
cd fastapi-demo

# Run the setup script (this does everything!)
bash setup.sh

# Start the server
make dev
```

That's it! Visit http://localhost:8000/docs to see the API documentation.

## Alternative: Manual Setup

```bash
# 1. Install dependencies
uv sync

# 2. Copy environment file
cp .env.example .env

# 3. Initialize database
make db-init

# 4. Start server
make dev
```

## What You Get

- ✅ FastAPI server running on http://localhost:8000
- ✅ Interactive API docs at http://localhost:8000/docs
- ✅ SQLite database with Users table
- ✅ Full CRUD API for users
- ✅ Alembic migrations set up and ready

## Try It Out

### Create a user:
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","username":"john","full_name":"John Doe"}'
```

### Get all users:
```bash
curl "http://localhost:8000/users/"
```

### Or just use the interactive docs:
Open http://localhost:8000/docs and click "Try it out" on any endpoint!

## Common Tasks

```bash
# Start server
make dev

# Create a migration after changing models
make db-migrate MSG="your description"

# Apply migrations
make db-upgrade

# Run tests
make test

# Clean everything and start fresh
make clean
make db-init
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide
- See example code in `app/` directory
- Modify or add new models, schemas, and endpoints

## Need Help?

All commands available:
```bash
make help
```

Full documentation in README.md
