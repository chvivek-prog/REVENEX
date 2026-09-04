
from __future__ import annotations

from typing import Any


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def build_dispute_intelligence(
    disputes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Read-only dispute intelligence.

    REVENEX identifies dispute state, exposure, urgency,
    and recommended review priority.

    It does not submit evidence, accept disputes,
    issue refunds, or mutate provider state.
    """

    results: list[dict[str, Any]] = []

    for index, dispute in enumerate(disputes):

        dispute_id = str(
            dispute.get("dispute_id")
            or dispute.get("id")
            or f"dispute-{index + 1}"
        )

        amount = _money(
            dispute.get("amount")
            or dispute.get("dispute_amount")
        )

        status = str(
            dispute.get("status")
            or "unknown"
        ).strip().lower()

        reason = str(
            dispute.get("reason")
            or dispute.get("reason_code")
            or "unknown"
        )

        if status in {
            "won",
            "resolved",
            "closed_won",
            "accepted",
        }:
            signal = "DISPUTE_RESOLVED"
            risk = "LOW"
            priority = "LOW"

        elif status in {
            "lost",
            "closed_lost",
            "reversed",
        }:
            signal = "DISPUTE_LOSS"
            risk = "HIGH"
            priority = "HIGH"

        elif status in {
            "open",
            "created",
            "needs_response",
            "under_review",
        }:
            signal = "DISPUTE_REVIEW_REQUIRED"
            risk = "HIGH"
            priority = "HIGH"

        elif status in {
            "pending",
            "processing",
        }:
            signal = "DISPUTE_PENDING"
            risk = "MEDIUM"
            priority = "MEDIUM"

        else:
            signal = "DISPUTE_UNKNOWN"
            risk = "MEDIUM"
            priority = "MEDIUM"

        results.append(
            {
                "dispute_id": dispute_id,
                "amount": round(amount, 2),
                "status": status,
                "reason": reason,
                "risk_level": risk,
                "priority": priority,
                "dispute_signal": signal,
                "read_only": True,
                "human_review_required": (
                    priority == "HIGH"
                ),
            }
        )

    return results


def summarize_dispute_behavior(
    disputes: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(disputes)

    open_count = sum(
        item["dispute_signal"]
        == "DISPUTE_REVIEW_REQUIRED"
        for item in disputes
    )

    lost_count = sum(
        item["dispute_signal"]
        == "DISPUTE_LOSS"
        for item in disputes
    )

    resolved_count = sum(
        item["dispute_signal"]
        == "DISPUTE_RESOLVED"
        for item in disputes
    )

    exposure = round(
        sum(item["amount"] for item in disputes),
        2,
    )

    open_exposure = round(
        sum(
            item["amount"]
            for item in disputes
            if item["dispute_signal"]
            == "DISPUTE_REVIEW_REQUIRED"
        ),
        2,
    )

    lost_exposure = round(
        sum(
            item["amount"]
            for item in disputes
            if item["dispute_signal"]
            == "DISPUTE_LOSS"
        ),
        2,
    )

    return {
        "total_disputes": total,
        "open_disputes": open_count,
        "lost_disputes": lost_count,
        "resolved_disputes": resolved_count,
        "total_dispute_exposure": exposure,
        "open_dispute_exposure": open_exposure,
        "lost_dispute_exposure": lost_exposure,
        "human_review_required": open_count > 0,
        "read_only": True,
    }
