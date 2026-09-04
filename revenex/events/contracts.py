
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RevenueEvent:
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    created_at: int | None
    payload_hash: str
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False



@dataclass(frozen=True)
class ProviderEvent:
    event_id: str
    provider: str
    event_type: str
    occurred_at: str
    payload: dict[str, Any]
    signature: str | None = None
    sandbox: bool = True



@dataclass(frozen=True)
class NormalizedEvent:
    event_id: str
    provider: str
    event_type: str
    occurred_at: str
    resource_type: str
    resource_id: str | None
    action: str
    payload: dict[str, Any]
    sandbox: bool = True


@dataclass(frozen=True)
class EventIngestionResult:
    accepted: bool
    duplicate: bool
    verified: bool
    status: str
    event_id: str
    provider: str
    event_type: str
    normalized: dict[str, Any]
    error: str | None = None


def normalize_revenue_event(
    payload: dict[str, Any],
) -> RevenueEvent:
    import hashlib
    import json

    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()

    event_id = str(
        payload.get(
            "id",
            payload.get("event_id", ""),
        )
    )

    event_type = str(
        payload.get(
            "event",
            payload.get("event_type", "UNKNOWN"),
        )
    )

    nested = payload.get("payload", {})

    entity_type = "unknown"
    entity_id = ""

    if isinstance(nested, dict):
        for key, value in nested.items():
            if isinstance(value, dict):
                entity_type = key.split(".")[0]
                entity = value.get("entity", value)
                if isinstance(entity, dict):
                    entity_id = str(
                        entity.get("id", "")
                    )
                break

    return RevenueEvent(
        event_id=event_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        created_at=payload.get("created_at"),
        payload_hash=hashlib.sha256(raw).hexdigest(),
    )
