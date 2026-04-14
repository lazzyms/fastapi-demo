from sqlalchemy import Column, String

from app.core.database import Base


class AppState(Base):
    """Key-value store for persistent application state (e.g., Gmail historyId)."""

    __tablename__ = "app_state"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
