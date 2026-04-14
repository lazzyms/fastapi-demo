from typing import Optional

from sqlalchemy.orm import Session

from app.models.app_state import AppState


def get_value(db: Session, key: str) -> Optional[str]:
    """Return the stored value for the given key, or None if not found."""
    row = db.query(AppState).filter(AppState.key == key).first()
    return row.value if row else None


def set_value(db: Session, key: str, value: str) -> None:
    """Upsert a key-value pair in app_state."""
    row = db.query(AppState).filter(AppState.key == key).first()
    if row:
        row.value = value
    else:
        row = AppState(key=key, value=value)
        db.add(row)
    db.commit()
