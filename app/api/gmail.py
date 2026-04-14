from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.schemas.emails import (
    GmailLabelResponse,
    LabelsSyncResponse,
    ThreadSyncResponse,
)
from app.services.gmail import (
    ensure_custom_labels,
    fetch_threads_last_10_days,
    get_gmail_service,
    list_gmail_labels,
)

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
