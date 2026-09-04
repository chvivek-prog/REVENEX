
from __future__ import annotations

from typing import Any


def normalize_provider_response(
    response: Any,
) -> dict[str, Any]:

    return {
        "provider": response.provider,
        "operation": response.operation,
        "success": bool(response.success),
        "status": response.status,
        "data": dict(response.data),
        "error": response.error,
        "request_id": response.request_id,
        "sandbox": bool(response.sandbox),
    }
