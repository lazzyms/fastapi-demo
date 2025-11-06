# FastAPI Demo - Interview Skeleton Project

A production-ready FastAPI project template with SQLite, SQLAlchemy, Alembic migrations, and Pydantic validation. Perfect for technical interviews and rapid prototyping.

## Features

- ✨ FastAPI with automatic OpenAPI documentation
- 🗄️ SQLite database with SQLAlchemy ORM
- 🔄 Alembic for database migrations
- ✅ Pydantic for data validation
- 📦 UV for fast, reliable package management
- 🎯 Sample CRUD API for Users
- 🛠️ Makefile for common tasks
- 🚀 One-command setup script

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

### Option 1: One-Command Setup (Recommended)

```bash
git clone <repository-url>
cd fastapi-demo
bash setup.sh
```

Then start the server:
```bash
make dev
```

### Option 2: Manual Setup

1. **Clone and navigate to the project**
   ```bash
   git clone <repository-url>
   cd fastapi-demo
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` if needed (default settings work out of the box).

4. **Initialize the database**
   ```bash
   make db-init
   ```

5. **Start the development server**
   ```bash
   make dev
   ```

### Access the Application

Once running, visit:
- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8000/redoc
- **Root Endpoint**: http://localhost:8000/

## Project Structure

```
fastapi-demo/
├── app/
│   ├── api/              # API route handlers
│   │   └── users.py      # User endpoints
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings management
│   │   └── database.py   # Database setup
│   ├── crud/             # Database operations
│   │   └── user.py       # User CRUD operations
│   ├── models/           # SQLAlchemy models
│   │   └── user.py       # User model
│   ├── schemas/          # Pydantic schemas
│   │   └── user.py       # User schemas
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic configuration
├── tests/                # Test directory
├── .env.example          # Example environment variables
├── alembic.ini          # Alembic configuration
├── pyproject.toml       # Project dependencies
├── Makefile             # Common commands
├── setup.sh             # Setup script
└── README.md            # This file
```

## Available Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make setup         # Complete setup (install + env + db)
make dev           # Start development server
make db-init       # Initialize database
make db-migrate    # Create new migration (use MSG='description')
make db-upgrade    # Apply pending migrations
make clean         # Remove database and cache files
make test          # Run tests
```

## API Endpoints

### Users

- `POST /users/` - Create a new user
- `GET /users/` - List all users (supports pagination)
- `GET /users/{user_id}` - Get a specific user
- `PATCH /users/{user_id}` - Update a user
- `DELETE /users/{user_id}` - Delete a user

### Health Check

- `GET /` - Root endpoint with API info
- `GET /health` - Health check endpoint

## Usage Examples

### Creating a User

```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "full_name": "John Doe"
  }'
```

### Getting All Users

```bash
curl "http://localhost:8000/users/"
```

### Getting a Specific User

```bash
curl "http://localhost:8000/users/1"
```

### Updating a User

```bash
curl -X PATCH "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Smith"
  }'
```

### Deleting a User

```bash
curl -X DELETE "http://localhost:8000/users/1"
```

## Adding New Models and Features

### Step 1: Create a New Model

Create a new file in `app/models/` (e.g., `app/models/post.py`):

```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Post(Base):
    """Post model."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    author = relationship("User", backref="posts")
```

Update `app/models/__init__.py`:
```python
from app.models.user import User
from app.models.post import Post

__all__ = ["User", "Post"]
```

### Step 2: Create Pydantic Schemas

Create `app/schemas/post.py`:

```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    author_id: int


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class PostResponse(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
```

### Step 3: Create CRUD Operations

Create `app/crud/post.py`:

```python
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate


def get_post(db: Session, post_id: int) -> Optional[Post]:
    return db.query(Post).filter(Post.id == post_id).first()


def get_posts(db: Session, skip: int = 0, limit: int = 100) -> List[Post]:
    return db.query(Post).offset(skip).limit(limit).all()


def create_post(db: Session, post: PostCreate) -> Post:
    db_post = Post(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_post(db: Session, post_id: int, post: PostUpdate) -> Optional[Post]:
    db_post = get_post(db, post_id)
    if not db_post:
        return None

    update_data = post.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)

    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: int) -> bool:
    db_post = get_post(db, post_id)
    if not db_post:
        return False

    db.delete(db_post)
    db.commit()
    return True
```

### Step 4: Create API Endpoints

Create `app/api/posts.py`:

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import post as crud_post
from app.schemas.post import PostCreate, PostUpdate, PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    return crud_post.create_post(db=db, post=post)


@router.get("/", response_model=List[PostResponse])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_post.get_posts(db, skip=skip, limit=limit)


@router.get("/{post_id}", response_model=PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = crud_post.get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@router.patch("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post: PostUpdate, db: Session = Depends(get_db)):
    db_post = crud_post.update_post(db, post_id=post_id, post=post)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    success = crud_post.delete_post(db, post_id=post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
```

Register the router in `app/main.py`:
```python
from app.api.posts import router as posts_router

app.include_router(posts_router)
```

### Step 5: Generate and Apply Migration

After creating your new models, generate a migration:

```bash
# Generate migration with a descriptive message
make db-migrate MSG="Add posts table"

# Or manually:
uv run alembic revision --autogenerate -m "Add posts table"
```

Apply the migration:

```bash
# Apply migrations
make db-upgrade

# Or manually:
uv run alembic upgrade head
```

**Important**: Always review the generated migration file in `alembic/versions/` before applying it to ensure it captures your intended changes correctly.

### Step 6: Test Your New Endpoints

Visit http://localhost:8000/docs to see your new endpoints in the interactive API documentation.

## Database Migrations with Alembic

### Common Migration Commands

```bash
# Create a new migration after model changes
make db-migrate MSG="Your migration description"

# Apply all pending migrations
make db-upgrade

# Manually create a migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback last migration
uv run alembic downgrade -1

# Show current migration version
uv run alembic current

# Show migration history
uv run alembic history
```

### Migration Best Practices

1. **Always review generated migrations** - Alembic's autogenerate is smart but not perfect
2. **Use descriptive messages** - Makes it easy to understand what each migration does
3. **Test migrations** - Apply them to a test database first
4. **Don't edit applied migrations** - Create a new migration to fix issues
5. **Commit migrations to version control** - Keep your schema changes tracked

### Adding Fields to Existing Models

1. Add the new field to your model class
2. Generate a migration: `make db-migrate MSG="Add field_name to table_name"`
3. Review the migration file
4. Apply the migration: `make db-upgrade`

Example of adding a field:
```python
# In app/models/user.py
class User(Base):
    # ... existing fields ...
    bio = Column(Text, nullable=True)  # New field
```

Then run:
```bash
make db-migrate MSG="Add bio field to users"
make db-upgrade
```

## Development Tips

### Running in Development Mode

The development server includes auto-reload:
```bash
make dev
```

### Manual Server Start

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Database Management

```bash
# Reset database (careful: deletes all data!)
make clean
make db-init

# View database
sqlite3 app.db
```

### Environment Variables

The `.env` file supports these variables:
- `APP_NAME` - Application name (default: "FastAPI Demo")
- `DEBUG` - Debug mode (default: true)
- `DATABASE_URL` - Database connection string (default: "sqlite:///./app.db")

## Testing

Add tests in the `tests/` directory. Run tests with:

```bash
make test
```

Example test file (`tests/test_users.py`):
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_user():
    response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
```

## Interview Tips

This project is designed to showcase:

1. **Clean Architecture** - Separation of concerns with layers (API, CRUD, Models, Schemas)
2. **Type Safety** - Pydantic schemas for validation
3. **Database Migrations** - Professional workflow with Alembic
4. **API Documentation** - Auto-generated with FastAPI
5. **Best Practices** - Environment variables, proper error handling, RESTful design

### Common Interview Tasks

You can easily demonstrate:
- Adding new endpoints
- Creating relationships between models
- Implementing filtering and sorting
- Adding authentication (JWT)
- Writing tests
- Error handling
- Input validation
- Database queries and optimization

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Locked
```bash
# Stop all running servers and try again
# Or delete the database and reinitialize:
make clean
make db-init
```

### Import Errors
```bash
# Reinstall dependencies
uv sync
```

### Migration Issues
```bash
# Check current migration state
uv run alembic current

# View migration history
uv run alembic history

# If needed, reset migrations (warning: loses data)
rm -rf alembic/versions/*.py
make clean
make db-init
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [UV Documentation](https://github.com/astral-sh/uv)

## License

MIT
