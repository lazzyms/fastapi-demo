# Development Guide

This guide is optimized for AI coding assistants (Claude, Cursor, etc.) and developers to quickly understand the project structure and common workflows.

## Project Architecture

### Core Components

1. **Models** (`app/models/`) - SQLAlchemy ORM models defining database tables
2. **Schemas** (`app/schemas/`) - Pydantic models for request/response validation
3. **CRUD** (`app/crud/`) - Database operations (Create, Read, Update, Delete)
4. **API** (`app/api/`) - FastAPI route handlers
5. **Core** (`app/core/`) - Configuration and database setup

### Data Flow

```
Request → API Route → Schema Validation → CRUD Operation → Model → Database
Database → Model → CRUD Operation → Schema Serialization → API Response
```

## Common Workflows

### 1. Adding a New Resource (e.g., "Post")

#### File Checklist:
- [ ] `app/models/post.py` - Database model
- [ ] `app/schemas/post.py` - Pydantic schemas
- [ ] `app/crud/post.py` - CRUD operations
- [ ] `app/api/posts.py` - API endpoints
- [ ] Update `app/models/__init__.py`
- [ ] Update `app/schemas/__init__.py`
- [ ] Update `app/crud/__init__.py`
- [ ] Register router in `app/main.py`
- [ ] Generate migration
- [ ] Apply migration

#### Step-by-Step:

**Step 1: Create Model** (`app/models/post.py`)
```python
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Step 2: Create Schemas** (`app/schemas/post.py`)
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PostResponse(PostBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

**Step 3: Create CRUD** (`app/crud/post.py`)
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

**Step 4: Create API Routes** (`app/api/posts.py`)
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

**Step 5: Register Router** (in `app/main.py`)
```python
from app.api.posts import router as posts_router
app.include_router(posts_router)
```

**Step 6: Generate and Apply Migration**
```bash
uv run alembic revision --autogenerate -m "Add posts table"
uv run alembic upgrade head
```

### 2. Adding Relationships

Example: Adding a relationship between User and Post

**In Post Model:**
```python
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class Post(Base):
    # ... other fields ...
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")
```

**In User Model:**
```python
from sqlalchemy.orm import relationship

class User(Base):
    # ... other fields ...
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
```

**Then generate migration:**
```bash
uv run alembic revision --autogenerate -m "Add user-post relationship"
uv run alembic upgrade head
```

### 3. Adding Fields to Existing Models

**Step 1:** Add field to model
```python
# app/models/user.py
class User(Base):
    # ... existing fields ...
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
```

**Step 2:** Add to schema
```python
# app/schemas/user.py
class UserBase(BaseModel):
    # ... existing fields ...
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
```

**Step 3:** Generate and apply migration
```bash
uv run alembic revision --autogenerate -m "Add bio and avatar_url to users"
uv run alembic upgrade head
```

### 4. Adding Query Filtering

Example: Get posts by author

**In CRUD:**
```python
def get_posts_by_author(db: Session, author_id: int) -> List[Post]:
    return db.query(Post).filter(Post.author_id == author_id).all()
```

**In API:**
```python
@router.get("/author/{author_id}", response_model=List[PostResponse])
def read_posts_by_author(author_id: int, db: Session = Depends(get_db)):
    return crud_post.get_posts_by_author(db, author_id=author_id)
```

### 5. Adding Search/Filtering

**CRUD with filters:**
```python
def get_posts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    author_id: Optional[int] = None
) -> List[Post]:
    query = db.query(Post)

    if search:
        query = query.filter(Post.title.contains(search))

    if author_id:
        query = query.filter(Post.author_id == author_id)

    return query.offset(skip).limit(limit).all()
```

**API with query parameters:**
```python
@router.get("/", response_model=List[PostResponse])
def read_posts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    author_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return crud_post.get_posts(
        db, skip=skip, limit=limit, search=search, author_id=author_id
    )
```

## Database Migration Patterns

### Creating Migrations

```bash
# After any model changes
uv run alembic revision --autogenerate -m "Description of changes"

# Review the generated file in alembic/versions/
# Then apply:
uv run alembic upgrade head
```

### Migration Commands Reference

```bash
# Create migration
uv run alembic revision --autogenerate -m "message"

# Apply all pending migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Rollback to specific version
uv run alembic downgrade <revision_id>

# Show current version
uv run alembic current

# Show history
uv run alembic history

# Show SQL without executing
uv run alembic upgrade head --sql
```

### Common Migration Scenarios

**Add Column:**
```python
op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
```

**Add Index:**
```python
op.create_index('idx_users_email', 'users', ['email'])
```

**Add Foreign Key:**
```python
op.add_column('posts', sa.Column('author_id', sa.Integer(), nullable=False))
op.create_foreign_key('fk_posts_author', 'posts', 'users', ['author_id'], ['id'])
```

**Drop Column:**
```python
op.drop_column('users', 'old_column')
```

## Testing Patterns

### Test File Structure

Create tests in `tests/` directory:

```python
# tests/test_users.py
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

def test_get_user():
    # Create user first
    create_response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User"
        }
    )
    user_id = create_response.json()["id"]

    # Get user
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id
```

## Common Commands Quick Reference

```bash
# Development
make dev                              # Start server
make clean                            # Clean database and cache

# Dependencies
uv sync                               # Install dependencies
uv add <package>                      # Add new dependency
uv remove <package>                   # Remove dependency

# Database
make db-init                          # Initialize database
make db-migrate MSG="message"         # Create migration
make db-upgrade                       # Apply migrations
uv run alembic current                # Show current migration
uv run alembic history                # Show migration history

# Testing
make test                             # Run tests
uv run pytest -v                      # Run tests verbose
uv run pytest tests/test_file.py      # Run specific test file
```

## File Templates

### Quick Copy-Paste Templates

Use these as starting points:

**Minimal Model:**
```python
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
```

**Minimal Schema:**
```python
from pydantic import BaseModel, ConfigDict

class ResourceBase(BaseModel):
    name: str

class ResourceCreate(ResourceBase):
    pass

class ResourceResponse(ResourceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

**Minimal CRUD:**
```python
from sqlalchemy.orm import Session
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate

def get_resource(db: Session, resource_id: int):
    return db.query(Resource).filter(Resource.id == resource_id).first()

def create_resource(db: Session, resource: ResourceCreate):
    db_resource = Resource(**resource.model_dump())
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource
```

**Minimal API:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud import resource as crud
from app.schemas.resource import ResourceCreate, ResourceResponse

router = APIRouter(prefix="/resources", tags=["resources"])

@router.post("/", response_model=ResourceResponse)
def create_resource(resource: ResourceCreate, db: Session = Depends(get_db)):
    return crud.create_resource(db=db, resource=resource)

@router.get("/{resource_id}", response_model=ResourceResponse)
def read_resource(resource_id: int, db: Session = Depends(get_db)):
    return crud.get_resource(db, resource_id=resource_id)
```

## Tips for AI Assistants

1. **Always follow the layer pattern**: Model → Schema → CRUD → API
2. **Update `__init__.py` files** when adding new modules
3. **Generate migrations** after model changes
4. **Use proper HTTP status codes**: 201 for creation, 204 for deletion
5. **Include proper error handling** with HTTPException
6. **Use `model_dump()` instead of deprecated `dict()`** for Pydantic v2
7. **Use `ConfigDict(from_attributes=True)`** instead of deprecated `orm_mode`

## Environment Configuration

### .env File Structure

```env
APP_NAME=FastAPI Demo
DEBUG=true
DATABASE_URL=sqlite:///./app.db
```

### Accessing Settings

```python
from app.core.config import settings

print(settings.database_url)
print(settings.app_name)
```

## Debugging

### Enable SQL Logging

In `app/core/database.py`:
```python
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=True  # Add this for SQL logging
)
```

### Interactive Database Session

```bash
sqlite3 app.db
.tables
.schema users
SELECT * FROM users;
.quit
```

### Python REPL Testing

```python
# Start Python REPL with uv
uv run python

from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
users = db.query(User).all()
print(users)
```
