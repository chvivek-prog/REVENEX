
from __future__ import annotations

import hashlib
import json
from typing import Any


def build_idempotency_key(
    operation: str,
    payload: dict[str, Any],
) -> str:

    canonical = json.dumps(
        {
            "operation": operation,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return f"revenex-{digest}"
