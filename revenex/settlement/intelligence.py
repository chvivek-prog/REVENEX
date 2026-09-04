
from __future__ import annotations

from typing import Any


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def build_settlement_intelligence(
    settlements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Deterministic read-only settlement intelligence.

    No settlement is triggered, modified, or reconciled externally.
    """

    results = []

    for index, settlement in enumerate(settlements):
        settlement_id = str(
            settlement.get("settlement_id")
            or settlement.get("id")
            or f"settlement-{index + 1}"
        )

        amount = _money(
            settlement.get("amount")
            or settlement.get("settlement_amount")
        )

        status = str(
            settlement.get("status")
            or "unknown"
        ).strip().lower()

        expected_amount = _money(
            settlement.get("expected_amount")
            or settlement.get("expected_settlement")
        )

        # Razorpay settlement reconciliation metadata.
        # Read-only normalization only; no provider mutation.
        utr = str(
            settlement.get("utr")
            or settlement.get("utr_number")
            or settlement.get("settlement_utr")
            or ""
        ).strip()

        fee = _money(
            settlement.get("fee")
            if settlement.get("fee") is not None
            else settlement.get("fees")
        )

        tax = _money(
            settlement.get("tax")
            if settlement.get("tax") is not None
            else settlement.get("tax_amount")
        )

        net_amount = round(
            max(0.0, amount - fee - tax),
            2,
        )

        if expected_amount > 0:
            variance = amount - expected_amount
            variance_ratio = variance / expected_amount
        else:
            variance = 0.0
            variance_ratio = 0.0

        if status in {
            "processed",
            "processed_successfully",
            "completed",
            "settled",
        }:
            signal = "SETTLEMENT_RECEIVED"
            risk = "LOW"

        elif status in {
            "pending",
            "created",
            "initiated",
        }:
            signal = "SETTLEMENT_PENDING"
            risk = "MEDIUM"

        elif status in {
            "failed",
            "reversed",
            "cancelled",
        }:
            signal = "SETTLEMENT_EXCEPTION"
            risk = "HIGH"

        else:
            signal = "SETTLEMENT_REVIEW"
            risk = "MEDIUM"

        if abs(variance_ratio) > 0.05:
            signal = "SETTLEMENT_VARIANCE_REVIEW"
            risk = "HIGH"

        results.append(
            {
                "settlement_id": settlement_id,
                "amount": round(amount, 2),
                "expected_amount": round(expected_amount, 2),
                "utr": utr,
                "fee": round(fee, 2),
                "tax": round(tax, 2),
                "net_amount": net_amount,
                "variance": round(variance, 2),
                "variance_ratio": round(
                    variance_ratio,
                    4,
                ),
                "status": status,
                "risk_level": risk,
                "settlement_signal": signal,
                "read_only": True,
            }
        )

    return results


def summarize_settlement_behavior(
    settlements: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(settlements)

    received = sum(
        1
        for item in settlements
        if item["settlement_signal"]
        == "SETTLEMENT_RECEIVED"
    )

    pending = sum(
        1
        for item in settlements
        if item["settlement_signal"]
        == "SETTLEMENT_PENDING"
    )

    exceptions = sum(
        1
        for item in settlements
        if item["settlement_signal"]
        in {
            "SETTLEMENT_EXCEPTION",
            "SETTLEMENT_VARIANCE_REVIEW",
        }
    )

    amount = round(
        sum(item["amount"] for item in settlements),
        2,
    )

    pending_amount = round(
        sum(
            item["amount"]
            for item in settlements
            if item["settlement_signal"]
            == "SETTLEMENT_PENDING"
        ),
        2,
    )

    variance = round(
        sum(item["variance"] for item in settlements),
        2,
    )

    return {
        "total_settlements": total,
        "received_settlements": received,
        "pending_settlements": pending,
        "exception_settlements": exceptions,
        "settlement_value": amount,
        "pending_settlement_value": pending_amount,
        "net_settlement_variance": variance,
        "read_only": True,
    }
