
from __future__ import annotations

from typing import Any


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def build_cash_intelligence(
    *,
    payments: list[dict[str, Any]] | None = None,
    refunds: list[dict[str, Any]] | None = None,
    settlements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Deterministic cash-flow intelligence.

    This is analytical only. It does not move money.
    """

    payments = payments or []
    refunds = refunds or []
    settlements = settlements or []

    captured = round(
        sum(
            _money(payment.get("amount"))
            for payment in payments
            if str(
                payment.get("status", "")
            ).lower()
            in {
                "captured",
                "paid",
                "success",
                "successful",
            }
        ),
        2,
    )

    refund_value = round(
        sum(
            _money(refund.get("amount"))
            for refund in refunds
        ),
        2,
    )

    settlement_value = round(
        sum(
            _money(settlement.get("amount"))
            for settlement in settlements
        ),
        2,
    )

    pending_settlement = round(
        sum(
            _money(settlement.get("amount"))
            for settlement in settlements
            if str(
                settlement.get("status", "")
            ).lower()
            in {
                "pending",
                "created",
                "initiated",
            }
        ),
        2,
    )

    net_payment_value = round(
        captured - refund_value,
        2,
    )

    cash_at_risk = round(
        refund_value + pending_settlement,
        2,
    )

    return {
        "captured_payment_value": captured,
        "refund_value": refund_value,
        "net_payment_value": net_payment_value,
        "settlement_value": settlement_value,
        "pending_settlement_value": pending_settlement,
        "cash_at_risk": cash_at_risk,
        "read_only": True,
    }
