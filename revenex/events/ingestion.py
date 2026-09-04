
from __future__ import annotations

import json
from typing import Any

from revenex.events.contracts import (
    EventIngestionResult,
    ProviderEvent,
)
from revenex.events.normalization import (
    normalize_event,
)
from revenex.events.signature import (
    verify_signature,
)
from revenex.events.store import (
    EventStore,
)


class EventIngestionEngine:

    def __init__(
        self,
        *,
        store: EventStore | None = None,
        provider_secrets: dict[str, str] | None = None,
    ) -> None:

        self.store = store or EventStore()

        self.provider_secrets = (
            dict(provider_secrets or {})
        )

    def ingest(
        self,
        *,
        event_id: str,
        provider: str,
        event_type: str,
        occurred_at: str,
        payload: dict[str, Any],
        signature: str | None = None,
        raw_body: bytes | None = None,
        sandbox: bool = True,
    ) -> EventIngestionResult:

        secret = self.provider_secrets.get(
            provider
        )

        if secret:

            body = (
                raw_body
                if raw_body is not None
                else json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )

            verified = verify_signature(
                secret,
                body,
                signature,
            )

            if not verified:
                return EventIngestionResult(
                    accepted=False,
                    duplicate=False,
                    verified=False,
                    status="INVALID_SIGNATURE",
                    event_id=event_id,
                    provider=provider,
                    event_type=event_type,
                    normalized={},
                    error="Webhook signature verification failed.",
                )

        else:
            verified = False

        if self.store.exists(event_id):

            return EventIngestionResult(
                accepted=True,
                duplicate=True,
                verified=verified,
                status="DUPLICATE_IGNORED",
                event_id=event_id,
                provider=provider,
                event_type=event_type,
                normalized={},
            )

        event = ProviderEvent(
            event_id=event_id,
            provider=provider,
            event_type=event_type,
            occurred_at=occurred_at,
            payload=dict(payload),
            signature=signature,
            sandbox=sandbox,
        )

        normalized = normalize_event(event)

        inserted = self.store.append(
            normalized
        )

        if not inserted:

            return EventIngestionResult(
                accepted=True,
                duplicate=True,
                verified=verified,
                status="DUPLICATE_IGNORED",
                event_id=event_id,
                provider=provider,
                event_type=event_type,
                normalized={},
            )

        return EventIngestionResult(
            accepted=True,
            duplicate=False,
            verified=verified,
            status="ACCEPTED",
            event_id=event_id,
            provider=provider,
            event_type=event_type,
            normalized={
                "event_id": normalized.event_id,
                "provider": normalized.provider,
                "event_type": normalized.event_type,
                "occurred_at": normalized.occurred_at,
                "resource_type": normalized.resource_type,
                "resource_id": normalized.resource_id,
                "action": normalized.action,
                "payload": normalized.payload,
                "sandbox": normalized.sandbox,
            },
        )

    def replay(
        self,
        event_id: str,
    ) -> dict[str, Any] | None:

        event = self.store.get(event_id)

        if event is None:
            return None

        return {
            "event_id": event["event_id"],
            "provider": event["provider"],
            "event_type": event["event_type"],
            "resource_type": event["resource_type"],
            "resource_id": event["resource_id"],
            "action": event["action"],
            "payload": event["payload"],
            "sandbox": event["sandbox"],
            "replay_only": True,
            "financial_mutation": False,
        }
