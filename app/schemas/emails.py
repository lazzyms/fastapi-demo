from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class GmailLabelResponse(BaseModel):
    id: str
    name: str
    message_list_visibility: Optional[str] = None
    label_list_visibility: Optional[str] = None
    type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LabelSyncResult(BaseModel):
    name: str
    existed: bool
    created: bool
    label_id: Optional[str] = None


class LabelsSyncResponse(BaseModel):
    results: list[LabelSyncResult]
    total: int
    already_existed: int
    newly_created: int


class ThreadSyncResponse(BaseModel):
    message: str
    status: str


class ThreadMessage(BaseModel):
    message_id: str
    thread_id: str
    sender: str
    date: str
    subject: str
    body: str
    position: int


class ThreadProcessingResult(BaseModel):
    thread_id: str
    message_count: int
    summary: str
    label: str
    label_id: Optional[str] = None


class PubSubMessage(BaseModel):
    """A single Pub/Sub push message as sent by Google Cloud."""

    message_id: str = Field(alias="messageId")
    data: str  # base64-encoded {"emailAddress": ..., "historyId": ...}
    publish_time: str = Field(alias="publishTime")
    attributes: Optional[dict] = None

    model_config = ConfigDict(populate_by_name=True)


class PubSubWebhookPayload(BaseModel):
    """Outer envelope of a Gmail Pub/Sub push notification."""

    message: PubSubMessage
    subscription: str


class WebhookAcceptedResponse(BaseModel):
    message: str
    status: str
