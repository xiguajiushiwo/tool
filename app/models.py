from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


MessageKind = Literal["quote", "supply", "demand", "unknown"]


class MessageEnvelope(BaseModel):
    message_id: str = Field(min_length=1)
    chat_id: str = "local-test"
    sender_id: str = "local-user"
    text: str = Field(min_length=1)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StructuredRecord(BaseModel):
    kind: MessageKind
    customer: str | None = None
    product: str | None = None
    model_spec: str | None = None
    quantity: str | None = None
    unit_price: str | None = None
    sale_price: str | None = None
    currency: str = "CNY"
    deadline: str | None = None
    delivery: str | None = None
    warranty: str | None = None
    notes: str | None = None
    source_chat_id: str
    source_message_id: str
    platform_url: str | None = None
    status: Literal["draft", "needs_review", "failed"] = "needs_review"
    raw_text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict[str, Any] = Field(default_factory=dict)


class DevMessageRequest(BaseModel):
    message_id: str | None = None
    chat_id: str = "local-test"
    sender_id: str = "local-user"
    text: str = Field(min_length=1)


class ProcessResult(BaseModel):
    ok: bool
    message_id: str
    kind: MessageKind
    status: str
    message: str
    platform_url: str | None = None
    record: StructuredRecord | None = None
