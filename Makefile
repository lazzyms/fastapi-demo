.PHONY: help install setup db-init db-migrate db-upgrade db-seed dev clean test verify

help:
	@echo "FastAPI Demo - Available Commands"
	@echo "=================================="
	@echo "make install      - Install dependencies using uv"
	@echo "make setup        - Complete setup (install + env + db + seed)"
	@echo "make verify       - Verify setup is correct"
	@echo "make db-init      - Initialize database with Alembic"
	@echo "make db-migrate   - Create a new migration (use MSG='description')"
	@echo "make db-upgrade   - Apply pending migrations"
	@echo "make db-seed      - Seed database with sample data"
	@echo "make dev          - Start development server"
	@echo "make clean        - Remove database and cache files"
	@echo "make test         - Run tests"

install:
	@echo "Installing dependencies..."
	uv sync

setup:
	@echo "Running complete setup..."
	@bash setup.sh

db-init:
	@echo "Initializing database..."
	uv run alembic revision --autogenerate -m "Initial migration"
	uv run alembic upgrade head
	@echo "Database initialized!"

db-migrate:
	@echo "Creating new migration..."
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a migration message using MSG='your message'"; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(MSG)"

db-upgrade:
	@echo "Applying migrations..."
	uv run alembic upgrade head

dev:
	@echo "Starting development server..."
	@echo "API docs available at http://localhost:8000/docs"
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	@echo "Cleaning up..."
	rm -f app.db
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete!"

test:
	@echo "Running tests..."
	uv run pytest

db-seed:
	@echo "Seeding database with sample data..."
	uv run python seed_db.py

verify:
	@echo "Verifying setup..."
	@bash test_setup.sh
