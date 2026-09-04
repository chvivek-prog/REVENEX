
from __future__ import annotations

from typing import Any


def build_event_audit(
    result: Any,
) -> dict[str, Any]:

    return {
        "event_id": result.event_id,
        "provider": result.provider,
        "event_type": result.event_type,
        "accepted": result.accepted,
        "duplicate": result.duplicate,
        "verified": result.verified,
        "status": result.status,
        "error": result.error,
        "safety": {
            "financial_mutation": False,
            "provider_mutation": False,
            "automatic_action": False,
            "execution_allowed": False,
            "human_approval_required": True,
        },
    }
