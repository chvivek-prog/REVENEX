
from __future__ import annotations
from enum import Enum

from typing import Any


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def build_payout_intelligence(
    payouts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Read-only payout intelligence.

    REVENEX analyzes payout state but never initiates,
    approves, cancels, retries, or mutates a payout.
    """

    results: list[dict[str, Any]] = []

    for index, payout in enumerate(payouts):
        payout_id = str(
            payout.get("payout_id")
            or payout.get("id")
            or f"payout-{index + 1}"
        )

        amount = _money(
            payout.get("amount")
            or payout.get("payout_amount")
        )

        status = str(
            payout.get("status")
            or "unknown"
        ).strip().lower()

        destination = str(
            payout.get("destination")
            or payout.get("account")
            or "unknown"
        )

        if status in {
            "processed",
            "completed",
            "success",
            "successful",
            "paid",
        }:
            signal = "PAYOUT_COMPLETED"
            risk = "LOW"

        elif status in {
            "pending",
            "created",
            "queued",
            "processing",
        }:
            signal = "PAYOUT_PENDING"
            risk = "MEDIUM"

        elif status in {
            "failed",
            "reversed",
            "cancelled",
            "rejected",
        }:
            signal = "PAYOUT_EXCEPTION"
            risk = "HIGH"

        else:
            signal = "PAYOUT_REVIEW"
            risk = "MEDIUM"

        results.append(
            {
                "payout_id": payout_id,
                "amount": round(amount, 2),
                "status": status,
                "destination": destination,
                "risk_level": risk,
                "payout_signal": signal,
                "read_only": True,
            }
        )

    return results

class PayoutLifecycle(str, Enum):
    """Deterministic payout lifecycle classification."""

    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


def _payout_lifecycle(payout: dict[str, Any]) -> PayoutLifecycle:
    """Classify payout state without performing any mutation."""

    status = str(
        payout.get("status", "")
    ).strip().lower()

    if status in {"completed", "processed", "paid", "success", "successful"}:
        return PayoutLifecycle.COMPLETED

    if status in {"pending", "created", "queued", "scheduled"}:
        return PayoutLifecycle.PENDING

    if status in {"processing", "in_progress", "initiated"}:
        return PayoutLifecycle.PROCESSING

    if status in {"failed", "failure", "rejected"}:
        return PayoutLifecycle.FAILED

    if status in {"reversed", "reversal", "cancelled", "canceled"}:
        return PayoutLifecycle.REVERSED

    return PayoutLifecycle.UNKNOWN


def classify_payout_lifecycles(
    payouts: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Return read-only payout lifecycle and idempotency awareness."""

    items = list(payouts or [])
    lifecycle_counts = {
        lifecycle.value: 0
        for lifecycle in PayoutLifecycle
    }

    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()

    for index, payout in enumerate(items):
        lifecycle = _payout_lifecycle(payout)
        lifecycle_counts[lifecycle.value] += 1

        payout_id = str(
            payout.get("id")
            or payout.get("payout_id")
            or payout.get("reference_id")
            or f"index:{index}"
        )

        if payout_id in seen_ids:
            duplicate_ids.add(payout_id)

        seen_ids.add(payout_id)

    return {
        "total_payouts": len(items),
        "lifecycle_counts": lifecycle_counts,
        "duplicate_payout_count": len(duplicate_ids),
        "duplicate_payout_ids": sorted(duplicate_ids),
        "idempotency_awareness": True,
        "read_only": True,
        "human_review_required": True,
        "execution_allowed": False,
        "automatic_action": False,
        "financial_mutation": False,
        "provider_mutation": False,
    }



def summarize_payout_behavior(
    payouts: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(payouts)

    completed = sum(
        item["payout_signal"] == "PAYOUT_COMPLETED"
        for item in payouts
    )

    pending = sum(
        item["payout_signal"] == "PAYOUT_PENDING"
        for item in payouts
    )

    exceptions = sum(
        item["payout_signal"] == "PAYOUT_EXCEPTION"
        for item in payouts
    )

    value = round(
        sum(item["amount"] for item in payouts),
        2,
    )

    pending_value = round(
        sum(
            item["amount"]
            for item in payouts
            if item["payout_signal"] == "PAYOUT_PENDING"
        ),
        2,
    )

    exception_value = round(
        sum(
            item["amount"]
            for item in payouts
            if item["payout_signal"] == "PAYOUT_EXCEPTION"
        ),
        2,
    )

    return {
        "total_payouts": total,
        "completed_payouts": completed,
        "pending_payouts": pending,
        "exception_payouts": exceptions,
        "payout_value": value,
        "pending_payout_value": pending_value,
        "exception_payout_value": exception_value,
        "read_only": True,
    }
