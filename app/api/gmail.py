import base64
import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.crud import app_state as crud_app_state
from app.schemas.emails import (
    GmailLabelResponse,
    LabelsSyncResponse,
    PubSubWebhookPayload,
    ThreadSyncResponse,
    WebhookAcceptedResponse,
)
from app.services.gmail import (
    ensure_custom_labels,
    fetch_history_since,
    fetch_threads_last_10_days,
    get_gmail_service,
    list_gmail_labels,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gmail", tags=["gmail"])


def get_service() -> Any:
    """FastAPI dependency that returns an authenticated Gmail service."""
    try:
        return get_gmail_service()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


# @router.get("/labels", response_model=list[GmailLabelResponse])
# def get_labels(service: Any = Depends(get_service)):
#     """List all labels in the authenticated Gmail account."""
#     raw_labels = list_gmail_labels(service)
#     return [
#         GmailLabelResponse(
#             id=label["id"],
#             name=label["name"],
#             message_list_visibility=label.get("messageListVisibility"),
#             label_list_visibility=label.get("labelListVisibility"),
#             type=label.get("type"),
#         )
#         for label in raw_labels
#     ]


# @router.get("/labels/sync", response_model=LabelsSyncResponse)
# def sync_labels(service: Any = Depends(get_service)):
#     """Ensure all custom labels exist in Gmail, creating any that are missing.

#     Returns a summary of which labels already existed and which were created.
#     """
#     return ensure_custom_labels(service)


@router.post(
    "/threads/sync",
    response_model=ThreadSyncResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_threads(
    background_tasks: BackgroundTasks,
    service: Any = Depends(get_service),
):
    """Kick off a background job that paginates Gmail threads from the last 10 days."""
    background_tasks.add_task(fetch_threads_last_10_days, service)
    return ThreadSyncResponse(
        message="Thread sync started. Fetching threads from the last 10 days.",
        status="accepted",
    )


# ---------------------------------------------------------------------------
# Gmail push-notification webhook
# ---------------------------------------------------------------------------

_GMAIL_HISTORY_ID_KEY = "gmail_history_id"


def _process_new_threads(service: Any, history_id: str, db: Session) -> None:
    """Background task: fetch threads since last known historyId and process each one."""
    last_history_id = crud_app_state.get_value(db, _GMAIL_HISTORY_ID_KEY)

    # First-ever notification: use the previous historyId (current - 1) as baseline
    # so the History API returns at least the triggering message.
    if last_history_id is None:
        last_history_id = str(max(int(history_id) - 1, 1))
        logger.info("No prior historyId in DB; bootstrapping from %s", last_history_id)

    logger.info(
        "Processing history from %s (notification historyId: %s)",
        last_history_id,
        history_id,
    )

    thread_ids = fetch_history_since(service, last_history_id)
    logger.info("Found %d new thread(s) to process.", len(thread_ids))

    for thread_id in thread_ids:
        try:
            thread = (
                service.users()
                .threads()
                .get(userId="me", id=thread_id, format="full")
                .execute()
            )
            raw_messages = thread.get("messages", [])

            from app.agents.thread_pipeline import process_thread  # noqa: PLC0415

            result = process_thread(service, thread_id, raw_messages)
            logger.info(
                "Webhook → thread %s processed: label='%s' (%d messages)",
                thread_id,
                result.label,
                result.message_count,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to process thread %s: %s", thread_id, exc)

    # Persist the latest historyId so next webhook call picks up from here
    crud_app_state.set_value(db, _GMAIL_HISTORY_ID_KEY, history_id)
    logger.info("Updated stored historyId to %s", history_id)


@router.post(
    "/webhook",
    response_model=WebhookAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def gmail_webhook(
    payload: PubSubWebhookPayload,
    background_tasks: BackgroundTasks,
    token: str = Query(default=""),
    service: Any = Depends(get_service),
    db: Session = Depends(get_db),
):
    """Receive a Gmail Pub/Sub push notification and process the new thread.

    Register your Pub/Sub push subscription with the URL:
        https://<your-domain>/gmail/webhook?token=<WEBHOOK_SECRET>

    Gmail sends a base64-encoded payload containing the Gmail address and
    a historyId. The endpoint decodes it, validates the secret token, then
    kicks off a background task that:
      1. Queries the Gmail History API for messages added since the last
         known historyId (persisted in the app_state table).
      2. Fetches each new thread in full.
      3. Runs the summarisation + label-tagging pipeline on the thread.
      4. Updates the stored historyId so the next notification picks up
         exactly where this one left off.
    """
    if not settings.webhook_secret or token != settings.webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing webhook token.",
        )

    # Decode the Pub/Sub message data: base64 → JSON → historyId
    try:
        decoded = base64.b64decode(payload.message.data + "==").decode("utf-8")
        notification = json.loads(decoded)
        history_id: str = str(notification["historyId"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed Pub/Sub message data: {exc}",
        )

    background_tasks.add_task(_process_new_threads, service, history_id, db)

    return WebhookAcceptedResponse(
        message=f"Webhook received. Processing threads since historyId {history_id}.",
        status="accepted",
    )
