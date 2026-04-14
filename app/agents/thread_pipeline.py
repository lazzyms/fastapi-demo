"""Thread processing pipeline: Summarize → Classify → Label.

This module is intentionally standalone. You can call process_thread()
for any single thread without going through the bulk sync flow:

    from app.agents.thread_pipeline import process_thread

    service = get_gmail_service()
    result = process_thread(service, thread_id="...", raw_messages=[...])
"""

import logging
from typing import Any

from app.agents.classifier import run_classifier
from app.agents.summarizer import run_summarizer
from app.schemas.emails import ThreadProcessingResult
from app.services.gmail import (
    apply_label_to_thread,
    extract_message_content,
    get_label_id_by_name,
)

logger = logging.getLogger(__name__)


def process_thread(
    service: Any,
    thread_id: str,
    raw_messages: list[dict],
) -> ThreadProcessingResult:
    """Summarize a thread, classify it, and apply the Gmail label.

    This function is fully self-contained and can be called independently
    for any thread without involving the bulk sync job.

    Args:
        service:      Authenticated Gmail API service (from get_gmail_service()).
        thread_id:    Gmail thread ID string.
        raw_messages: List of raw message dicts returned by the Gmail API
                      (format="full" — must include payload/headers/body).

    Returns:
        ThreadProcessingResult with the summary, assigned label, and label_id.
    """
    logger.info("Processing thread %s (%d messages)", thread_id, len(raw_messages))

    # 1. Extract structured content from raw Gmail message dicts
    messages = [extract_message_content(m) for m in raw_messages]

    # Sort by position to guarantee chronological order
    messages.sort(key=lambda m: m.position)

    # 2. Agent 1 — summarize
    logger.debug("Thread %s: running summarizer", thread_id)
    summary = run_summarizer(messages)

    # 3. Agent 2 — classify
    logger.debug("Thread %s: running classifier", thread_id)
    label = run_classifier(summary)

    # 4. Resolve the label ID and apply it to the thread
    label_id = get_label_id_by_name(service, label)

    if label_id:
        apply_label_to_thread(service, thread_id, label_id)
        logger.info("Thread %s labelled as '%s' (%s)", thread_id, label, label_id)
    else:
        logger.warning(
            "Thread %s: label '%s' not found in Gmail — skipping label application",
            thread_id,
            label,
        )

    return ThreadProcessingResult(
        thread_id=thread_id,
        message_count=len(messages),
        summary=summary,
        label=label,
        label_id=label_id,
    )
