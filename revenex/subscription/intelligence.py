
from __future__ import annotations

from typing import Any


ACTIVE_STATES = {
    "active",
    "authenticated",
    "pending",
    "created",
}

RISK_STATES = {
    "halted",
    "cancelled",
    "expired",
    "completed",
}


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def build_subscription_intelligence(
    subscriptions: list[dict[str, Any]],
    payments: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Build deterministic recurring-revenue intelligence.

    Read-only:
      - no subscription creation
      - no cancellation
      - no plan mutation
      - no provider mutation
    """

    payments = payments or []

    results = []

    for index, subscription in enumerate(subscriptions):
        subscription_id = str(
            subscription.get("subscription_id")
            or subscription.get("id")
            or f"subscription-{index + 1}"
        )

        customer_id = str(
            subscription.get("customer_id")
            or subscription.get("customer")
            or "unknown-customer"
        )

        status = str(
            subscription.get("status")
            or "created"
        ).strip().lower()

        plan_amount = _money(
            subscription.get("plan_amount")
            or subscription.get("amount")
            or subscription.get("total_amount")
        )

        paid_cycles = int(
            subscription.get("paid_count")
            or subscription.get("paid_cycles")
            or 0
        )

        total_cycles = int(
            subscription.get("total_count")
            or subscription.get("total_cycles")
            or 0
        )

        remaining_cycles = max(
            0,
            total_cycles - paid_cycles,
        )

        if status in RISK_STATES:
            renewal_risk = "HIGH"
            signal = "SUBSCRIPTION_AT_RISK"
        elif status in ACTIVE_STATES:
            renewal_risk = "LOW"
            signal = "RECURRING_REVENUE_ACTIVE"
        else:
            renewal_risk = "MEDIUM"
            signal = "SUBSCRIPTION_REVIEW"

        recurring_exposure = round(
            plan_amount * remaining_cycles,
            2,
        )

        results.append(
            {
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "status": status,
                "plan_amount": round(plan_amount, 2),
                "paid_cycles": paid_cycles,
                "total_cycles": total_cycles,
                "remaining_cycles": remaining_cycles,
                "recurring_revenue_exposure": recurring_exposure,
                "renewal_risk": renewal_risk,
                "subscription_signal": signal,
                "read_only": True,
            }
        )

    return results


def summarize_subscription_behavior(
    subscriptions: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(subscriptions)

    active = sum(
        1
        for item in subscriptions
        if item["subscription_signal"]
        == "RECURRING_REVENUE_ACTIVE"
    )

    at_risk = sum(
        1
        for item in subscriptions
        if item["subscription_signal"]
        == "SUBSCRIPTION_AT_RISK"
    )

    exposure = round(
        sum(
            item["recurring_revenue_exposure"]
            for item in subscriptions
        ),
        2,
    )

    return {
        "total_subscriptions": total,
        "active_subscriptions": active,
        "at_risk_subscriptions": at_risk,
        "recurring_revenue_exposure": exposure,
        "read_only": True,
    }
