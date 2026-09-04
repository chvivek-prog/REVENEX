
from __future__ import annotations

import hashlib
import hmac
from typing import Any


def verify_webhook_signature(
    *,
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    if not signature or not secret:
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    supplied = signature.strip()

    if supplied.startswith("sha256="):
        supplied = supplied[7:]

    return hmac.compare_digest(
        expected,
        supplied,
    )


def normalize_webhook_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    event_type = str(
        payload.get("event")
        or payload.get("event_type")
        or "unknown"
    )

    entity = payload.get("entity")

    if isinstance(entity, dict):
        entity_id = (
            entity.get("id")
            or entity.get("entity_id")
            or ""
        )
    else:
        entity_id = (
            payload.get("entity_id")
            or payload.get("id")
            or ""
        )

    return {
        "event_type": event_type,
        "entity_id": str(entity_id),
        "payload": dict(payload),
    }
