
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Callable


@dataclass(frozen=True)
class WebhookEvent:
    event_id: str
    event_type: str
    entity_id: str
    payload: dict[str, Any]
    received_at: str
    source: str
    signature_verified: bool


def event_fingerprint(
    event_type: str,
    entity_id: str,
    payload: dict[str, Any],
) -> str:
    canonical = json.dumps(
        {
            "event_type": event_type,
            "entity_id": entity_id,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return sha256(canonical).hexdigest()


def create_webhook_event(
    *,
    event_type: str,
    entity_id: str,
    payload: dict[str, Any],
    source: str = "provider",
    signature_verified: bool = False,
    event_id: str | None = None,
) -> WebhookEvent:
    fingerprint = event_fingerprint(
        event_type,
        entity_id,
        payload,
    )

    return WebhookEvent(
        event_id=str(event_id or fingerprint),
        event_type=str(event_type),
        entity_id=str(entity_id),
        payload=dict(payload),
        received_at=datetime.now(
            timezone.utc
        ).isoformat(),
        source=str(source),
        signature_verified=bool(
            signature_verified
        ),
    )


class EventBus:
    """
    In-memory deterministic event bus.

    Phase 8 intentionally does not execute financial actions.
    """

    def __init__(self) -> None:
        self._handlers: dict[
            str,
            list[Callable[[WebhookEvent], Any]],
        ] = {}
        self._seen: set[str] = set()

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[WebhookEvent], Any],
    ) -> None:
        self._handlers.setdefault(
            event_type,
            [],
        ).append(handler)

    def publish(
        self,
        event: WebhookEvent,
    ) -> bool:
        if event.event_id in self._seen:
            return False

        self._seen.add(event.event_id)

        for handler in self._handlers.get(
            event.event_type,
            [],
        ):
            handler(event)

        return True

    @property
    def processed_event_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._seen))
