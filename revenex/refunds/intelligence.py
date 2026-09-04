
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

    results: list[dict[str, Any]] = []

    for index, refund in enumerate(refunds):

        refund_id = str(
            refund.get("refund_id")
            or refund.get("id")
            or f"refund-{index + 1}"
        )

        amount = _money(
            refund.get("amount")
            or refund.get("refund_amount")
        )

        status = str(
            refund.get("status")
            or "unknown"
        ).strip().lower()

        reason = str(
            refund.get("reason")
            or "unknown"
        )

        if status in {
            "processed",
            "completed",
            "success",
            "successful",
        }:
            signal = "REFUND_COMPLETED"
            risk = "LOW"

        elif status in {
            "pending",
            "processing",
            "created",
        }:
            signal = "REFUND_PENDING"
            risk = "MEDIUM"

        elif status in {
            "failed",
            "reversed",
            "rejected",
        }:
            signal = "REFUND_EXCEPTION"
            risk = "HIGH"

        else:
            signal = "REFUND_REVIEW"
            risk = "MEDIUM"

        results.append(
            {
                "refund_id": refund_id,
                "amount": round(amount, 2),
                "status": status,
                "reason": reason,
                "risk_level": risk,
                "refund_signal": signal,
                "read_only": True,
                "human_review_required": (
                    signal
                    in {
                        "REFUND_EXCEPTION",
                        "REFUND_REVIEW",
                    }
                ),
            }
        )

    return results


def summarize_refund_behavior(
    refunds: list[dict[str, Any]],
) -> dict[str, Any]:

    return {
        "total_refunds": len(refunds),
        "completed_refunds": sum(
            r["refund_signal"]
            == "REFUND_COMPLETED"
            for r in refunds
        ),
        "pending_refunds": sum(
            r["refund_signal"]
            == "REFUND_PENDING"
            for r in refunds
        ),
        "exception_refunds": sum(
            r["refund_signal"]
            == "REFUND_EXCEPTION"
            for r in refunds
        ),
        "refund_value": round(
            sum(r["amount"] for r in refunds),
            2,
        ),
        "pending_refund_value": round(
            sum(
                r["amount"]
                for r in refunds
                if r["refund_signal"]
                == "REFUND_PENDING"
            ),
            2,
        ),
        "exception_refund_value": round(
            sum(
                r["amount"]
                for r in refunds
                if r["refund_signal"]
                == "REFUND_EXCEPTION"
            ),
            2,
        ),
        "read_only": True,
    }
