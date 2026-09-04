
from __future__ import annotations

from typing import Any


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def build_refund_intelligence(
    refunds: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Deterministic read-only refund intelligence.

    No refund is created, cancelled, processed, or mutated.
    """

    results = []

    for index, refund in enumerate(refunds):
        refund_id = str(
            refund.get("refund_id")
            or refund.get("id")
            or f"refund-{index + 1}"
        )

        customer_id = str(
            refund.get("customer_id")
            or refund.get("customer")
            or "unknown-customer"
        )

        amount = _money(
            refund.get("amount")
            or refund.get("refund_amount")
        )

        status = str(
            refund.get("status")
            or "unknown"
        ).strip().lower()

        if status in {
            "processed",
            "processed_successfully",
            "completed",
            "success",
        }:
            risk = "LOW"
            signal = "REFUND_COMPLETED"

        elif status in {
            "failed",
            "cancelled",
            "rejected",
        }:
            risk = "MEDIUM"
            signal = "REFUND_FAILED"

        elif status in {
            "pending",
            "created",
            "initiated",
        }:
            risk = "MEDIUM"
            signal = "REFUND_PENDING"

        else:
            risk = "MEDIUM"
            signal = "REFUND_REVIEW"

        results.append(
            {
                "refund_id": refund_id,
                "customer_id": customer_id,
                "amount": round(amount, 2),
                "status": status,
                "risk_level": risk,
                "refund_signal": signal,
                "read_only": True,
            }
        )

    return results


def summarize_refund_behavior(
    refunds: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(refunds)

    completed = sum(
        1
        for refund in refunds
        if refund["refund_signal"]
        == "REFUND_COMPLETED"
    )

    pending = sum(
        1
        for refund in refunds
        if refund["refund_signal"]
        == "REFUND_PENDING"
    )

    failed = sum(
        1
        for refund in refunds
        if refund["refund_signal"]
        == "REFUND_FAILED"
    )

    amount = round(
        sum(refund["amount"] for refund in refunds),
        2,
    )

    pending_amount = round(
        sum(
            refund["amount"]
            for refund in refunds
            if refund["refund_signal"]
            == "REFUND_PENDING"
        ),
        2,
    )

    return {
        "total_refunds": total,
        "completed_refunds": completed,
        "pending_refunds": pending,
        "failed_refunds": failed,
        "refund_value": amount,
        "pending_refund_exposure": pending_amount,
        "read_only": True,
    }
