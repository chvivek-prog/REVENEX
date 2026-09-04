
from __future__ import annotations

from typing import Any


def build_exception_governance(
    *,
    disputes: dict[str, Any],
    refunds: dict[str, Any],
    settlements: dict[str, Any],
) -> dict[str, Any]:

    dispute_count = int(
        disputes.get("open_disputes", 0)
    )

    refund_count = int(
        refunds.get("exception_refunds", 0)
    )

    settlement_count = int(
        settlements.get("exception_count", 0)
    )

    total = (
        dispute_count
        + refund_count
        + settlement_count
    )

    if total == 0:
        priority = "NORMAL"
        action = "MONITOR"
    elif total <= 2:
        priority = "MEDIUM"
        action = "REVIEW_EXCEPTIONS"
    else:
        priority = "HIGH"
        action = "EXECUTIVE_REVIEW"

    return {
        "exception_count": total,
        "priority": priority,
        "recommended_action": action,
        "human_approval_required": True,
        "automatic_action": False,
        "financial_mutation": False,
        "provider_mutation": False,
        "read_only": True,
    }
