# Claude AI Assistant Guide for FastAPI Demo

This document helps Claude (and other AI assistants) understand the project structure and provide better assistance to developers working on this codebase.

## Project Overview

**Type**: FastAPI REST API with SQLite database
**Purpose**: Interview skeleton project / rapid prototyping template
**Architecture**: Layered (Model → Schema → CRUD → API)
**Database**: SQLite with SQLAlchemy ORM
**Migrations**: Alembic
**Validation**: Pydantic v2
**Package Manager**: uv

## Key Characteristics

1. **Clean Architecture**: Clear separation of concerns across layers
2. **Type Safety**: Extensive use of Python type hints and Pydantic validation
3. **Professional Patterns**: Production-ready code structure
4. **Interview-Ready**: Designed to showcase best practices
5. **Extensible**: Easy to add new features following established patterns

## Understanding the Codebase

### Architecture Layers

The project follows a strict layered architecture:

```
User Request
    ↓
API Layer (FastAPI routes) ← Validates input via Pydantic schemas
    ↓
CRUD Layer (Database operations) ← Business logic
    ↓
Model Layer (SQLAlchemy ORM) ← Data structure
    ↓
Database (SQLite)
```

### File Organization

```
app/
├── main.py              # Application entry point
├── api/                 # API route handlers (controllers)
│   ├── __init__.py
│   └── users.py         # User endpoints
├── core/                # Core configuration
│   ├── config.py        # Settings (from .env)
│   └── database.py      # Database setup
├── crud/                # Database operations (data access layer)
│   ├── __init__.py
│   └── user.py          # User CRUD operations
├── models/              # SQLAlchemy models (database schema)
│   ├── __init__.py
│   └── user.py          # User model
└── schemas/             # Pydantic models (validation/serialization)
    ├── __init__.py
    └── user.py          # User schemas
```

### Layer Responsibilities

#### 1. Models (`app/models/`)
- Define database table structure using SQLAlchemy
- Represent database tables as Python classes
- Define relationships between tables
- **Example**: `User` class defines the `users` table structure

#### 2. Schemas (`app/schemas/`)
- Validate incoming request data (Pydantic)
- Serialize database objects for API responses
- Define API contracts (what data is accepted/returned)
- **Always create 4 schemas**: Base, Create, Update, Response

#### 3. CRUD (`app/crud/`)
- Execute database queries and operations
- Implement business logic for data manipulation
- Keep database operations isolated from API layer
- **Common operations**: get, get_multi, create, update, delete

#### 4. API (`app/api/`)
- Define HTTP endpoints (routes)
- Handle HTTP requests and responses
- Orchestrate CRUD operations
- Return appropriate status codes and error messages

## Common Development Tasks

### How to Add a New Resource

When a developer wants to add a new resource (e.g., "Add a Posts feature"):

#### Step 1: Create the Model
**File**: `app/models/post.py`
```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    author = relationship("User", back_populates="posts")
```

**Don't forget**: Update `app/models/__init__.py`

#### Step 2: Create the Schemas
**File**: `app/schemas/post.py`
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

**Don't forget**: Update `app/schemas/__init__.py`

#### Step 3: Create CRUD Operations
**File**: `app/crud/post.py`
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

**Don't forget**: Update `app/crud/__init__.py`

#### Step 4: Create API Routes
**File**: `app/api/posts.py`
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
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post

@router.patch("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post: PostUpdate, db: Session = Depends(get_db)):
    db_post = crud_post.update_post(db, post_id=post_id, post=post)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    if not crud_post.delete_post(db, post_id=post_id):
        raise HTTPException(status_code=404, detail="Post not found")
```

**Don't forget**: Update `app/api/__init__.py`

#### Step 5: Register the Router
**File**: `app/main.py`
```python
from app.api.posts import router as posts_router
app.include_router(posts_router)
```

#### Step 6: Generate and Apply Migration
```bash
uv run alembic revision --autogenerate -m "Add posts table"
uv run alembic upgrade head
```

**CRITICAL**: Always generate migrations after modifying models!

### How to Add Fields to Existing Models

When a developer wants to add fields to an existing model:

1. **Update Model**: Add column to model class
2. **Update Schemas**: Add field to relevant schemas
3. **Generate Migration**: `make db-migrate MSG="Add field_name to table"`
4. **Apply Migration**: `make db-upgrade`

Example:
```python
# app/models/user.py
class User(Base):
    # ... existing fields ...
    bio = Column(Text, nullable=True)  # New field

# app/schemas/user.py
class UserBase(BaseModel):
    # ... existing fields ...
    bio: Optional[str] = None  # New field

# Then run:
# make db-migrate MSG="Add bio field to users"
# make db-upgrade
```

## Important Patterns and Conventions

### Pydantic v2 (Current Version)

**CORRECT** ✅
```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    data = user.model_dump()
```

**INCORRECT** ❌ (Deprecated v1 syntax)
```python
class User(BaseModel):
    class Config:
        orm_mode = True
    data = user.dict()
```

### HTTP Status Codes

- `200 OK` - GET, PATCH success
- `201 Created` - POST success
- `204 No Content` - DELETE success
- `400 Bad Request` - Business logic errors (duplicate email, etc.)
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Validation errors (automatic via Pydantic)

### Error Handling

**ALWAYS** use HTTPException, **NEVER** return None:

```python
# ✅ CORRECT
from fastapi import HTTPException

if not user:
    raise HTTPException(status_code=404, detail="User not found")

# ❌ WRONG
if not user:
    return None  # Don't do this in API routes!
```

### Database Operations

**ALWAYS** commit and refresh after modifications:

```python
# Create
db.add(db_obj)
db.commit()
db.refresh(db_obj)
return db_obj

# Update
for field, value in update_data.items():
    setattr(db_obj, field, value)
db.commit()
db.refresh(db_obj)
return db_obj

# Delete
db.delete(db_obj)
db.commit()
return True
```

## Understanding User Requests

### Typical User Requests and How to Handle Them

1. **"Add a new feature/resource"**
   - Follow the 6-step pattern above
   - Create all 4 layers: Model → Schema → CRUD → API
   - Generate migration
   - Suggest testing via `/docs`

2. **"Add a field to existing model"**
   - Update model class
   - Update relevant schemas
   - Generate and apply migration
   - Test via `/docs`

3. **"Add authentication"**
   - This is more complex - suggest creating separate auth module
   - Would need: password hashing, JWT tokens, auth dependencies

4. **"Add search/filtering"**
   - Modify CRUD function to accept filter parameters
   - Update API endpoint to accept query parameters
   - Example in DEVELOPMENT.md

5. **"Write tests"**
   - Unit tests for schemas/CRUD
   - Integration tests for API endpoints
   - E2E tests for complete workflows
   - Examples in `tests/` directory

## Testing Guidance

When users ask about testing:

- **Unit tests**: Test individual components (schemas, CRUD)
  - Location: `tests/unit/`
  - Run: `uv run pytest tests/unit/`

- **Integration tests**: Test API + database together
  - Location: `tests/integration/`
  - Run: `uv run pytest tests/integration/`

- **E2E tests**: Test complete user scenarios
  - Location: `tests/e2e/`
  - Run: `uv run pytest tests/e2e/`

All tests use an in-memory SQLite database for speed and isolation.

## Common Mistakes to Avoid

1. **Using Pydantic v1 syntax** - Always use v2
2. **Forgetting migrations** - Required after any model changes
3. **Returning None from API** - Use HTTPException instead
4. **Not updating `__init__.py`** - Required when adding new modules
5. **Not registering router** - Must add to `app/main.py`
6. **Wrong status codes** - Use 201 for POST, 204 for DELETE
7. **Missing type hints** - Always add type annotations

## Development Commands

```bash
# Setup
bash setup.sh              # Complete setup in one command
make setup                 # Alternative using Makefile

# Development
make dev                   # Start development server
make help                  # Show all available commands

# Database
make db-init              # Initialize database (first time)
make db-migrate MSG="..."  # Create migration
make db-upgrade           # Apply migrations
uv run alembic current    # Show current migration
uv run alembic history    # Show migration history

# Testing
make test                 # Run all tests
uv run pytest -v          # Verbose test output
uv run pytest tests/unit/ # Run only unit tests

# Cleanup
make clean                # Remove database and cache files
```

## Environment Variables

Configured in `.env` (copy from `.env.example`):

```env
APP_NAME=FastAPI Demo
DEBUG=true
DATABASE_URL=sqlite:///./app.db
```

Accessed via:
```python
from app.core.config import settings
print(settings.database_url)
```

## API Documentation

Once server is running:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Helping Developers Effectively

When a developer asks for help:

1. **Understand context**: What are they trying to build?
2. **Follow patterns**: Use the established architecture
3. **Be specific**: Provide complete code examples
4. **Include all steps**: Don't skip `__init__.py` updates or migrations
5. **Suggest testing**: Point them to `/docs` or test files
6. **Explain decisions**: Why this pattern? Why this status code?

## Example Interaction

**User**: "I want to add a Posts feature where users can create blog posts"

**Claude Response**:
1. Acknowledge: "I'll help you add a Posts resource with a relationship to Users"
2. Plan: List the 6 steps (Model, Schema, CRUD, API, Register, Migrate)
3. Execute: Create all necessary files with complete code
4. Migrations: Generate and apply migration commands
5. Testing: Suggest testing via `/docs` endpoint
6. Summary: "Created Posts feature with CRUD endpoints at `/posts/`"

## Additional Resources

- **README.md**: User-facing documentation
- **DEVELOPMENT.md**: Detailed development guide with examples
- **QUICK_START.md**: Fast setup guide
- **tests/README.md**: Testing documentation
- **.cursorrules**: Rules for Cursor AI
- **.clinerules**: Rules for Cline AI

## Project Philosophy

This project prioritizes:
1. **Clarity** over cleverness
2. **Consistency** over flexibility
3. **Explicit** over implicit
4. **Type safety** over dynamic typing
5. **Tested** over assumed working

Remember: This is an interview/showcase project. Code should demonstrate professional software engineering practices!
