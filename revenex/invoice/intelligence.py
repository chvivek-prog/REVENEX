
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


INVOICE_STATES = {
    "draft",
    "issued",
    "partially_paid",
    "paid",
    "cancelled",
    "expired",
    "deleted",
}


def _money(value: Any) -> float:
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, value)


def _days_overdue(invoice: dict[str, Any]) -> int:
    explicit = invoice.get("days_overdue")

    if explicit is not None:
        try:
            return max(0, int(explicit))
        except (TypeError, ValueError):
            pass

    due = (
        invoice.get("due_date")
        or invoice.get("expire_by")
        or invoice.get("expiry_date")
    )

    if not due:
        return 0

    try:
        if isinstance(due, (int, float)):
            due_dt = datetime.fromtimestamp(
                float(due),
                tz=timezone.utc,
            )
        else:
            raw = str(due).replace("Z", "+00:00")
            due_dt = datetime.fromisoformat(raw)
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        return max(0, (now.date() - due_dt.date()).days)
    except (TypeError, ValueError, OverflowError):
        return 0


def _status(invoice: dict[str, Any], outstanding: float, days: int) -> str:
    supplied = str(
        invoice.get("status", "")
    ).strip().lower()

    if supplied in INVOICE_STATES:
        return supplied

    if outstanding <= 0:
        return "paid"

    if days > 0:
        return "issued"

    return "issued"


def build_invoice_intelligence(
    invoices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert raw invoice records into deterministic,
    read-only revenue intelligence.

    This function never mutates invoices or financial state.
    """

    results: list[dict[str, Any]] = []

    for index, invoice in enumerate(invoices):
        amount = _money(
            invoice.get("amount")
            or invoice.get("gross_amount")
            or invoice.get("total_amount")
        )

        outstanding = _money(
            invoice.get("outstanding_amount")
            if invoice.get("outstanding_amount") is not None
            else invoice.get("amount_due")
            if invoice.get("amount_due") is not None
            else amount - _money(
                invoice.get("amount_paid")
            )
        )

        paid = max(0.0, amount - outstanding)
        days = _days_overdue(invoice)
        status = _status(invoice, outstanding, days)

        if amount > 0:
            payment_ratio = min(1.0, paid / amount)
        else:
            payment_ratio = 1.0

        # Deterministic invoice risk model.
        risk_score = 0.0

        if days >= 120:
            risk_score += 0.60
        elif days >= 90:
            risk_score += 0.50
        elif days >= 60:
            risk_score += 0.40
        elif days >= 30:
            risk_score += 0.25
        elif days > 0:
            risk_score += 0.10

        if outstanding > 0:
            risk_score += min(
                0.30,
                outstanding / max(amount, 1.0) * 0.30,
            )

        if payment_ratio < 0.25:
            risk_score += 0.10

        risk_score = min(1.0, risk_score)

        if risk_score >= 0.75:
            risk_level = "CRITICAL"
        elif risk_score >= 0.50:
            risk_level = "HIGH"
        elif risk_score >= 0.25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Conservative deterministic collection probability.
        collection_probability = max(
            0.0,
            min(
                1.0,
                1.0
                - risk_score * 0.65
                - (0.10 if days > 90 else 0.0),
            ),
        )

        expected_collection = round(
            outstanding * collection_probability,
            2,
        )

        remaining_exposure = round(
            max(
                0.0,
                outstanding - expected_collection,
            ),
            2,
        )

        if status in {"paid", "cancelled", "deleted", "expired"}:
            recommended_action = "MONITOR"
        elif risk_level == "CRITICAL":
            recommended_action = "AGGRESSIVE_RECOVERY_REVIEW"
        elif risk_level == "HIGH":
            recommended_action = "RECOVERY_REVIEW"
        elif risk_level == "MEDIUM":
            recommended_action = "FOLLOW_UP"
        else:
            recommended_action = "MONITOR"

        customer_id = (
            invoice.get("customer_id")
            or invoice.get("customer")
            or "unknown-customer"
        )

        invoice_id = (
            invoice.get("invoice_id")
            or invoice.get("id")
            or f"invoice-{index + 1}"
        )

        results.append(
            {
                "invoice_id": str(invoice_id),
                "customer_id": str(customer_id),
                "amount": round(amount, 2),
                "amount_paid": round(paid, 2),
                "amount_due": round(outstanding, 2),
                "outstanding_amount": round(outstanding, 2),
                "days_overdue": days,
                "status": status,
                "payment_ratio": round(payment_ratio, 4),
                "risk_score": round(risk_score, 4),
                "risk_level": risk_level,
                "collection_probability": round(
                    collection_probability,
                    4,
                ),
                "expected_collection": expected_collection,
                "remaining_exposure": remaining_exposure,
                "recommended_action": recommended_action,
                "read_only": True,
            }
        )

    return results
