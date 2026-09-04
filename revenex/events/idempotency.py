
from __future__ import annotations

import hashlib
import json
from typing import Any


def event_fingerprint(
    *,
    provider: str,
    event_type: str,
    payload: dict[str, Any],
) -> str:

    canonical = json.dumps(
        {
            "provider": provider,
            "event_type": event_type,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


class EventDeduplicator:

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def seen(
        self,
        event_id: str,
    ) -> bool:
        return event_id in self._seen

    def mark(
        self,
        event_id: str,
    ) -> None:
        self._seen.add(event_id)

    def check_and_mark(
        self,
        event_id: str,
    ) -> bool:

        if self.seen(event_id):
            return False

        self.mark(event_id)
        return True
