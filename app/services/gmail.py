import base64
import binascii
import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings, CUSTOM_GMAIL_LABELS
from app.schemas.emails import LabelSyncResult, LabelsSyncResponse, ThreadMessage

logger = logging.getLogger(__name__)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


class _StaticTokenCredentials(Credentials):
    """Static credentials that never expire and don't attempt to refresh.

    Prevents 'The credentials do not contain the necessary fields need to refresh'
    errors when using a long-lived or manually provided OAuth token.
    """

    def refresh(self, request):
        pass

    @property
    def expired(self):
        return False

    @property
    def valid(self):
        return True


def get_gmail_service() -> Any:
    """Build and return an authenticated Gmail API service client.

    Uses the OAuth2 access token stored in settings.google_api_key.
    """
    if not settings.google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Add a valid Gmail OAuth2 access token to your .env file."
        )
    creds = _StaticTokenCredentials(token=settings.google_api_key, scopes=GMAIL_SCOPES)
    return build("gmail", "v1", credentials=creds)


def list_gmail_labels(service: Any) -> list[dict]:
    """Return all labels for the authenticated Gmail account."""
    response = service.users().labels().list(userId="me").execute()
    return response.get("labels", [])


def get_label_name_map(service: Any) -> dict[str, str]:
    """Return a mapping of Gmail label name -> label ID."""
    return {label["name"]: label["id"] for label in list_gmail_labels(service)}


def create_gmail_label(service: Any, name: str) -> dict:
    """Create a Gmail label with the given name and return the created label object."""
    body = {
        "name": name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    return service.users().labels().create(userId="me", body=body).execute()


def ensure_custom_labels(service: Any) -> LabelsSyncResponse:
    """Check that all custom labels exist in Gmail; create any that are missing.

    Returns a LabelsSyncResponse summarising which labels already existed
    and which were newly created.
    """
    logger.info("Ensuring custom Gmail labels exist: %s", CUSTOM_GMAIL_LABELS)
    existing_labels = list_gmail_labels(service)
    existing_names: dict[str, str] = {
        label["name"]: label["id"] for label in existing_labels
    }

    results: list[LabelSyncResult] = []

    for label_name in CUSTOM_GMAIL_LABELS:
        if label_name in existing_names:
            results.append(
                LabelSyncResult(
                    name=label_name,
                    existed=True,
                    created=False,
                    label_id=existing_names[label_name],
                )
            )
            logger.info(
                "Label already exists: %s (%s)", label_name, existing_names[label_name]
            )
        else:
            try:
                created = create_gmail_label(service, label_name)
                results.append(
                    LabelSyncResult(
                        name=label_name,
                        existed=False,
                        created=True,
                        label_id=created.get("id"),
                    )
                )
                logger.info("Created label: %s (%s)", label_name, created.get("id"))
            except HttpError as exc:
                logger.error("Failed to create label '%s': %s", label_name, exc)
                results.append(
                    LabelSyncResult(
                        name=label_name,
                        existed=False,
                        created=False,
                        label_id=None,
                    )
                )

    return LabelsSyncResponse(
        results=results,
        total=len(results),
        already_existed=sum(1 for r in results if r.existed),
        newly_created=sum(1 for r in results if r.created),
    )


def extract_message_content(message: dict, position: int = 0) -> ThreadMessage:
    """Extract structured content from a raw Gmail API message dict (format='full')."""
    headers = {}
    payload = message.get("payload", {})
    for header in payload.get("headers", []):
        headers[header["name"].lower()] = header["value"]

    body = _extract_body(payload)

    return ThreadMessage(
        message_id=message.get("id", ""),
        thread_id=message.get("threadId", ""),
        sender=headers.get("from", "unknown"),
        date=headers.get("date", ""),
        subject=headers.get("subject", "(no subject)"),
        body=body,
        position=position,
    )


def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            # Gmail returns unpadded base64url; restore required padding first.
            padded_data = data + ("=" * (-len(data) % 4))
            try:
                return base64.urlsafe_b64decode(padded_data).decode(
                    "utf-8", errors="replace"
                )
            except (binascii.Error, ValueError) as exc:
                logger.warning("Failed to decode Gmail message body: %s", exc)
                return ""
        return ""

    # Multipart: recurse into parts, prefer text/plain
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            return _extract_body(part)
    # Fallback: return first non-empty part
    for part in parts:
        text = _extract_body(part)
        if text:
            return text
    return ""


def get_label_id_by_name(
    service: Any, label_name: str, label_name_map: dict[str, str] | None = None
) -> str | None:
    """Return the Gmail label ID for a given label name, or None if not found.

    If label_name_map is provided, this avoids an additional labels.list API call.
    """
    if label_name_map is not None:
        return label_name_map.get(label_name)
    return get_label_name_map(service).get(label_name)


def apply_label_to_thread(service: Any, thread_id: str, label_id: str) -> dict:
    """Apply a label to a Gmail thread and return the API response.

    Requires the gmail.modify scope on the authenticated token.
    """
    body = {"addLabelIds": [label_id], "removeLabelIds": []}
    return (
        service.users().threads().modify(userId="me", id=thread_id, body=body).execute()
    )


def fetch_history_since(service: Any, start_history_id: str) -> list[str]:
    """Return unique thread IDs for messages added since start_history_id.

    Uses the Gmail History API with historyTypes=messageAdded so we only
    react to new incoming messages, not label changes or deletions.
    """
    thread_ids: list[str] = []
    seen: set[str] = set()
    page_token: str | None = None

    while True:
        request_kwargs: dict = {
            "userId": "me",
            "startHistoryId": start_history_id,
            "historyTypes": ["messageAdded"],
        }
        if page_token:
            request_kwargs["pageToken"] = page_token

        try:
            response = service.users().history().list(**request_kwargs).execute()
        except HttpError as exc:
            logger.error(
                "History API error (startHistoryId=%s): %s", start_history_id, exc
            )
            break

        for history_record in response.get("history", []):
            for msg_added in history_record.get("messagesAdded", []):
                tid = msg_added.get("message", {}).get("threadId")
                if tid and tid not in seen:
                    seen.add(tid)
                    thread_ids.append(tid)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return thread_ids


def fetch_threads_last_10_days(service: Any) -> None:
    """Paginate through all Gmail threads from the last 10 days and process each message.

    Fetches 10 threads per page and iterates through every message in each thread.
    """
    query = "newer_than:10d"
    page_token: str | None = None
    page_number = 0

    label_name_map = get_label_name_map(service)

    while True:
        page_number += 1
        request_kwargs: dict = {
            "userId": "me",
            "q": query,
            "maxResults": 10,
        }
        if page_token:
            request_kwargs["pageToken"] = page_token

        response = service.users().threads().list(**request_kwargs).execute()
        threads = response.get("threads", [])

        if not threads:
            logger.info("Page %d: no threads found, stopping.", page_number)
            break

        logger.info("Page %d: fetched %d thread(s).", page_number, len(threads))

        for thread_meta in threads:
            thread = (
                service.users()
                .threads()
                .get(userId="me", id=thread_meta["id"], format="full")
                .execute()
            )
            raw_messages = thread.get("messages", [])

            try:
                from app.agents.thread_pipeline import process_thread

                result = process_thread(
                    service,
                    thread_meta["id"],
                    raw_messages,
                    label_name_map,
                )
                logger.info(
                    "Thread %s → label='%s' (%d messages)",
                    thread_meta["id"],
                    result.label,
                    result.message_count,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to process thread %s: %s", thread_meta["id"], exc)

        page_token = response.get("nextPageToken")
        if not page_token:
            logger.info("All pages processed. Total pages: %d.", page_number)
            break
