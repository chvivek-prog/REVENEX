from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EventStatus(str, Enum):
    RECEIVED = "RECEIVED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True)
class WebhookEvent:
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    payload_hash: str
    received_at: float
    status: EventStatus
    attempt_count: int = 0
    signature_verified: bool = False
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False

    def with_status(
        self,
        status: EventStatus,
        *,
        attempt_count: int | None = None,
        signature_verified: bool | None = None,
    ) -> "WebhookEvent":
        return WebhookEvent(
            event_id=self.event_id,
            event_type=self.event_type,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            payload_hash=self.payload_hash,
            received_at=self.received_at,
            status=status,
            attempt_count=(
                self.attempt_count
                if attempt_count is None
                else attempt_count
            ),
            signature_verified=(
                self.signature_verified
                if signature_verified is None
                else signature_verified
            ),
            read_only=True,
            financial_mutation=False,
            provider_mutation=False,
        )
