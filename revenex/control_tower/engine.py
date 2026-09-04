
from __future__ import annotations

from typing import Any


SAFETY_BOUNDARY = {
    "execution_allowed": False,
    "automatic_action": False,
    "financial_mutation": False,
    "provider_mutation": False,
    "human_approval_required": True,
}


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def build_control_tower(
    *,
    revenue: dict[str, Any] | None = None,
    invoices: dict[str, Any] | None = None,
    payments: dict[str, Any] | None = None,
    orders: dict[str, Any] | None = None,
    subscriptions: dict[str, Any] | None = None,
    refunds: dict[str, Any] | None = None,
    settlements: dict[str, Any] | None = None,
    disputes: dict[str, Any] | None = None,
    payouts: dict[str, Any] | None = None,
    webhooks: dict[str, Any] | None = None,
    reconciliation: dict[str, Any] | None = None,
    cash: dict[str, Any] | None = None,
    forecast: dict[str, Any] | None = None,
    outcomes: dict[str, Any] | None = None,
    learning: dict[str, Any] | None = None,
) -> dict[str, Any]:

    revenue = revenue or {}
    invoices = invoices or {}
    payments = payments or {}
    orders = orders or {}
    subscriptions = subscriptions or {}
    refunds = refunds or {}
    settlements = settlements or {}
    disputes = disputes or {}
    payouts = payouts or {}
    webhooks = webhooks or {}
    reconciliation = reconciliation or {}
    cash = cash or {}
    forecast = forecast or {}
    outcomes = outcomes or {}
    learning = learning or {}

    outstanding = _num(
        revenue.get("total_outstanding")
        or invoices.get("total_outstanding")
    )

    revenue_at_risk = _num(
        revenue.get("total_revenue_at_risk")
        or revenue.get("revenue_at_risk")
    )

    expected_collection = _num(
        revenue.get("expected_collection")
        or forecast.get("expected_collection")
    )

    exception_count = (
        int(disputes.get("open_disputes", 0))
        + int(refunds.get("exception_refunds", 0))
        + int(settlements.get("exception_count", 0))
        + int(reconciliation.get("exception_count", 0))
    )

    operational_alerts = (
        int(webhooks.get("failed_count", 0))
        + int(payouts.get("exception_count", 0))
        + int(payments.get("failed_payments", 0))
    )

    learning_signal = (
        learning.get("learning_signal")
        or outcomes.get("learning_signal")
        or "WAIT_FOR_OUTCOME"
    )

    if exception_count >= 5:
        executive_state = "CRITICAL"
    elif exception_count >= 2:
        executive_state = "ATTENTION_REQUIRED"
    elif revenue_at_risk > 0:
        executive_state = "REVENUE_RISK"
    else:
        executive_state = "STABLE"

    if exception_count or operational_alerts:
        priority = "HIGH"
    elif revenue_at_risk > 0:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return {
        "executive_state": executive_state,
        "priority": priority,

        "revenue": {
            "outstanding": round(outstanding, 2),
            "revenue_at_risk": round(revenue_at_risk, 2),
            "expected_collection": round(
                expected_collection,
                2,
            ),
        },

        "operations": {
            "exception_count": exception_count,
            "operational_alerts": operational_alerts,
            "webhook_failures": int(
                webhooks.get("failed_count", 0)
            ),
            "payout_exceptions": int(
                payouts.get("exception_count", 0)
            ),
            "payment_failures": int(
                payments.get("failed_payments", 0)
            ),
        },

        "customer_revenue": {
            "invoice_count": int(
                invoices.get("total_invoices", 0)
            ),
            "payment_count": int(
                payments.get("total_payments", 0)
            ),
            "order_count": int(
                orders.get("total_orders", 0)
            ),
            "active_subscriptions": int(
                subscriptions.get(
                    "active_subscriptions",
                    0,
                )
            ),
        },

        "risk": {
            "dispute_exposure": round(
                _num(
                    disputes.get(
                        "open_dispute_exposure"
                    )
                ),
                2,
            ),
            "refund_exposure": round(
                _num(
                    refunds.get(
                        "exception_refund_value"
                    )
                ),
                2,
            ),
            "settlement_exception_exposure": round(
                _num(
                    settlements.get(
                        "exception_exposure"
                    )
                ),
                2,
            ),
            "reconciliation_exceptions": int(
                reconciliation.get(
                    "exception_count",
                    0,
                )
            ),
        },

        "learning": {
            "signal": learning_signal,
            "evaluation_status": (
                learning.get(
                    "evaluation_status",
                    outcomes.get(
                        "evaluation_status",
                        "INSUFFICIENT_DATA",
                    ),
                )
            ),
            "confidence": _num(
                learning.get(
                    "learning_confidence",
                    0,
                )
            ),
            "automatic_model_mutation": False,
        },

        "pipeline": [
            "OBSERVE",
            "INVESTIGATE",
            "PREDICT",
            "SIMULATE",
            "DECIDE",
            "MONITOR",
            "LEARN",
            "AUDIT",
        ],

        "safety": dict(SAFETY_BOUNDARY),

        "read_only": True,
    }


def build_executive_summary(
    tower: dict[str, Any],
) -> str:

    state = tower["executive_state"]
    priority = tower["priority"]

    revenue = tower["revenue"]
    operations = tower["operations"]

    return (
        f"REVENEX state={state}. "
        f"Priority={priority}. "
        f"Outstanding revenue="
        f"₹{revenue['outstanding']:,.2f}. "
        f"Revenue at risk="
        f"₹{revenue['revenue_at_risk']:,.2f}. "
        f"Expected collection="
        f"₹{revenue['expected_collection']:,.2f}. "
        f"Exceptions="
        f"{operations['exception_count']}. "
        f"Operational alerts="
        f"{operations['operational_alerts']}. "
        f"Human approval remains required."
    )
