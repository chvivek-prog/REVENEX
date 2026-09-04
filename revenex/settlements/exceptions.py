
from __future__ import annotations

from typing import Any


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def analyze_settlement_exceptions(
    settlements: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    results: list[dict[str, Any]] = []

    for index, settlement in enumerate(settlements):

        settlement_id = str(
            settlement.get("settlement_id")
            or settlement.get("id")
            or f"settlement-{index + 1}"
        )

        expected = _money(
            settlement.get("expected_amount")
            or settlement.get("amount")
        )

        observed = _money(
            settlement.get("observed_amount")
            or settlement.get("settled_amount")
            or settlement.get("amount")
        )

        status = str(
            settlement.get("status")
            or "unknown"
        ).strip().lower()

        variance = round(
            observed - expected,
            2,
        )

        if status in {
            "processed",
            "completed",
            "settled",
        } and abs(variance) <= 1.0:
            exception = False
            signal = "SETTLEMENT_RECONCILED"
            severity = "LOW"

        elif abs(variance) > 1.0:
            exception = True
            signal = "SETTLEMENT_AMOUNT_VARIANCE"
            severity = "HIGH"

        elif status in {
            "failed",
            "reversed",
            "exception",
        }:
            exception = True
            signal = "SETTLEMENT_EXCEPTION"
            severity = "HIGH"

        elif status in {
            "pending",
            "processing",
        }:
            exception = True
            signal = "SETTLEMENT_PENDING"
            severity = "MEDIUM"

        else:
            exception = True
            signal = "SETTLEMENT_REVIEW"
            severity = "MEDIUM"

        results.append(
            {
                "settlement_id": settlement_id,
                "expected_amount": round(
                    expected,
                    2,
                ),
                "observed_amount": round(
                    observed,
                    2,
                ),
                "variance": variance,
                "status": status,
                "exception": exception,
                "severity": severity,
                "settlement_signal": signal,
                "read_only": True,
                "human_review_required": exception,
            }
        )

    return results


def summarize_settlement_exceptions(
    settlements: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(settlements)

    exceptions = [
        item
        for item in settlements
        if item["exception"]
    ]

    return {
        "total_settlements": total,
        "exception_count": len(exceptions),
        "reconciled_count": sum(
            not item["exception"]
            for item in settlements
        ),
        "exception_exposure": round(
            sum(
                abs(item["variance"])
                for item in exceptions
            ),
            2,
        ),
        "pending_count": sum(
            item["settlement_signal"]
            == "SETTLEMENT_PENDING"
            for item in settlements
        ),
        "variance_count": sum(
            item["settlement_signal"]
            == "SETTLEMENT_AMOUNT_VARIANCE"
            for item in settlements
        ),
        "human_review_required": bool(
            exceptions
        ),
        "read_only": True,
    }
