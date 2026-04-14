import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import users_router, gmail_router
from app.core.config import settings
from app.services.gmail import get_gmail_service, ensure_custom_labels

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before the app begins serving requests."""
    # Ensure custom Gmail labels exist on every startup
    try:
        logger.info("Starting up FastAPI Demo application...")
        service = get_gmail_service()
        sync_result = ensure_custom_labels(service)
        logger.info(
            "Gmail labels synced — existed: %d, created: %d",
            sync_result.already_existed,
            sync_result.newly_created,
        )
    except Exception as exc:
        logger.warning("Gmail label sync skipped: %s", exc)

    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
    description="FastAPI interview skeleton project with SQLite, Alembic, and CRUD operations",
    lifespan=lifespan,
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
app.include_router(gmail_router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to FastAPI Demo!", "docs": "/docs", "redoc": "/redoc"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
