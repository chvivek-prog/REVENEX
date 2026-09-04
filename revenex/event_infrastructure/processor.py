from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .contracts import (
    EventStatus,
    WebhookEvent,
)
from .store import EventStore
from .verification import WebhookVerifier


class EventProcessor:
    """
    Production-oriented event ingestion boundary.

    Responsibilities:
      - normalize payload
      - verify signature
      - deduplicate
      - persist
      - track processing state

    It deliberately does NOT execute financial/provider actions.
    """

    def __init__(
        self,
        *,
        store: EventStore,
        verifier: WebhookVerifier,
    ) -> None:
        self.store = store
        self.verifier = verifier

    @staticmethod
    def _entity(
        payload: dict[str, Any],
    ) -> tuple[str, str]:
        nested = payload.get("payload", {})

        if not isinstance(nested, dict):
            return "unknown", ""

        for key, value in nested.items():
            if not isinstance(value, dict):
                continue

            entity_type = key.split(".")[0]

            entity = value.get(
                "entity",
                value,
            )

            if isinstance(entity, dict):
                return (
                    entity_type,
                    str(entity.get("id", "")),
                )

        return "unknown", ""

    @staticmethod
    def _hash(
        payload: dict[str, Any],
    ) -> str:
        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

        return hashlib.sha256(raw).hexdigest()

    def ingest(
        self,
        *,
        payload: dict[str, Any],
        signature: str,
    ) -> WebhookEvent:
        event_id = str(
            payload.get(
                "id",
                payload.get("event_id", ""),
            )
        )

        if not event_id:
            raise ValueError(
                "Webhook event id is required"
            )

        event_type = str(
            payload.get(
                "event",
                payload.get(
                    "event_type",
                    "UNKNOWN",
                ),
            )
        )

        entity_type, entity_id = self._entity(
            payload
        )

        payload_bytes = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

        verified = self.verifier.verify(
            payload_bytes,
            signature,
        )

        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_hash=self._hash(payload),
            received_at=time.time(),
            status=(
                EventStatus.VERIFIED
                if verified
                else EventStatus.REJECTED
            ),
            signature_verified=verified,
        )

        if not verified:
            self.store.save(event)
            return event

        inserted = self.store.save(event)

        if not inserted:
            existing = self.store.get(event_id)

            if existing is None:
                raise RuntimeError(
                    "Duplicate event could not be recovered"
                )

            return existing.with_status(
                EventStatus.DUPLICATE,
                signature_verified=True,
            )

        return event

    def mark_processing(
        self,
        event_id: str,
    ) -> WebhookEvent:
        event = self.store.get(event_id)

        if event is None:
            raise KeyError(event_id)

        updated = event.with_status(
            EventStatus.PROCESSING,
            attempt_count=event.attempt_count + 1,
        )

        return self.store.update(updated)

    def mark_processed(
        self,
        event_id: str,
    ) -> WebhookEvent:
        event = self.store.get(event_id)

        if event is None:
            raise KeyError(event_id)

        return self.store.update(
            event.with_status(
                EventStatus.PROCESSED
            )
        )

    def mark_failed(
        self,
        event_id: str,
    ) -> WebhookEvent:
        event = self.store.get(event_id)

        if event is None:
            raise KeyError(event_id)

        return self.store.update(
            event.with_status(
                EventStatus.FAILED
            )
        )
