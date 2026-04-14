import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings, CUSTOM_GMAIL_LABELS
from app.models.emails import LabelSyncResult, LabelsSyncResponse

logger = logging.getLogger(__name__)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.readonly",
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


def fetch_threads_last_10_days(service: Any) -> None:
    """Paginate through all Gmail threads from the last 10 days and process each message.

    Fetches 10 threads per page and iterates through every message in each thread.
    """
    query = "newer_than:10d"
    page_token: str | None = None
    page_number = 0

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
                .get(userId="me", id=thread_meta["id"], format="metadata")
                .execute()
            )
            messages = thread.get("messages", [])

            for message in messages:
                # TODO: process each message (e.g. classify, label, store)
                logger.debug(
                    "Thread %s — message %s", thread_meta["id"], message.get("id")
                )

        page_token = response.get("nextPageToken")
        if not page_token:
            logger.info("All pages processed. Total pages: %d.", page_number)
            break
