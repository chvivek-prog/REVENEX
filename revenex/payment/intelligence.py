
from __future__ import annotations

from typing import Any


PAYMENT_STATUSES = {
    "created",
    "authorized",
    "captured",
    "failed",
    "refunded",
    "partially_refunded",
    "pending",
    "cancelled",
}


SUCCESS_STATUSES = {
    "captured",
    "paid",
    "success",
    "successful",
}


FAILURE_STATUSES = {
    "failed",
    "cancelled",
}


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _status(payment: dict[str, Any]) -> str:
    value = str(
        payment.get("status", "")
    ).strip().lower()

    if value:
        return value

    if payment.get("captured") is True:
        return "captured"

    if payment.get("success") is True:
        return "captured"

    return "pending"


def _customer_id(payment: dict[str, Any]) -> str:
    return str(
        payment.get("customer_id")
        or payment.get("customer")
        or "unknown-customer"
    )


def _invoice_id(payment: dict[str, Any]) -> str | None:
    value = (
        payment.get("invoice_id")
        or payment.get("invoice")
    )

    return None if value is None else str(value)


def build_payment_intelligence(
    payments: list[dict[str, Any]],
    invoices: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Build deterministic payment intelligence.

    This function is strictly read-only.

    It does not:
      - create payments
      - capture payments
      - refund payments
      - mutate provider state
      - mutate financial state
    """

    invoices = invoices or []

    invoice_due = {
        str(
            invoice.get("invoice_id")
            or invoice.get("id")
        ): _money(
            invoice.get("outstanding_amount")
            if invoice.get("outstanding_amount") is not None
            else invoice.get("amount_due")
        )
        for invoice in invoices
        if invoice.get("invoice_id") is not None
        or invoice.get("id") is not None
    }

    results: list[dict[str, Any]] = []

    for index, payment in enumerate(payments):
        amount = _money(
            payment.get("amount")
            or payment.get("amount_paid")
            or payment.get("value")
        )

        status = _status(payment)
        customer_id = _customer_id(payment)
        invoice_id = _invoice_id(payment)

        successful = status in SUCCESS_STATUSES
        failed = status in FAILURE_STATUSES

        matched_invoice_due = (
            invoice_due.get(invoice_id)
            if invoice_id is not None
            else None
        )

        if matched_invoice_due is not None:
            if matched_invoice_due <= 0:
                payment_coverage = 1.0
            else:
                payment_coverage = min(
                    1.0,
                    amount / matched_invoice_due,
                )
        else:
            payment_coverage = None

        # Payment quality is intentionally conservative.
        if successful and amount > 0:
            payment_risk_score = 0.0
        elif failed:
            payment_risk_score = 0.85
        elif status in {"pending", "authorized", "created"}:
            payment_risk_score = 0.40
        else:
            payment_risk_score = 0.30

        if amount <= 0:
            payment_risk_score = max(
                payment_risk_score,
                0.60,
            )

        if payment_risk_score >= 0.75:
            risk_level = "HIGH"
        elif payment_risk_score >= 0.40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if successful:
            payment_signal = "PAYMENT_REALIZED"
        elif failed:
            payment_signal = "PAYMENT_FAILED"
        elif status in {"pending", "authorized", "created"}:
            payment_signal = "PAYMENT_PENDING"
        else:
            payment_signal = "PAYMENT_REVIEW"

        results.append(
            {
                "payment_id": str(
                    payment.get("payment_id")
                    or payment.get("id")
                    or f"payment-{index + 1}"
                ),
                "customer_id": customer_id,
                "invoice_id": invoice_id,
                "amount": round(amount, 2),
                "status": status,
                "successful": successful,
                "failed": failed,
                "payment_coverage": (
                    None
                    if payment_coverage is None
                    else round(payment_coverage, 4)
                ),
                "risk_score": round(
                    payment_risk_score,
                    4,
                ),
                "risk_level": risk_level,
                "payment_signal": payment_signal,
                "read_only": True,
            }
        )

    return results


def summarize_payment_behavior(
    payment_intelligence: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate payment behavior without changing source data.
    """

    total = len(payment_intelligence)

    successful = sum(
        1
        for payment in payment_intelligence
        if payment["successful"]
    )

    failed = sum(
        1
        for payment in payment_intelligence
        if payment["failed"]
    )

    pending = sum(
        1
        for payment in payment_intelligence
        if payment["status"]
        in {"pending", "authorized", "created"}
    )

    realized_amount = round(
        sum(
            payment["amount"]
            for payment in payment_intelligence
            if payment["successful"]
        ),
        2,
    )

    attempted_amount = round(
        sum(
            payment["amount"]
            for payment in payment_intelligence
        ),
        2,
    )

    success_rate = (
        successful / total
        if total
        else 0.0
    )

    realization_rate = (
        realized_amount / attempted_amount
        if attempted_amount > 0
        else 0.0
    )

    if failed > successful and failed > 0:
        behavior_signal = "PAYMENT_FAILURE_PRESSURE"
    elif successful > 0:
        behavior_signal = "PAYMENT_BEHAVIOR_REALIZED"
    elif pending > 0:
        behavior_signal = "PAYMENT_OUTCOMES_PENDING"
    else:
        behavior_signal = "NO_PAYMENT_SIGNAL"

    return {
        "total_payments": total,
        "successful_payments": successful,
        "failed_payments": failed,
        "pending_payments": pending,
        "attempted_amount": attempted_amount,
        "realized_amount": realized_amount,
        "success_rate": round(success_rate, 4),
        "realization_rate": round(
            realization_rate,
            4,
        ),
        "behavior_signal": behavior_signal,
        "read_only": True,
    }
