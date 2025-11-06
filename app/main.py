from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import users_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
    description="FastAPI interview skeleton project with SQLite, Alembic, and CRUD operations"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "Welcome to FastAPI Demo!",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
