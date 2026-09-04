"""
REVENEX Stage 34 — Predictive Revenue Intelligence.

Transparent deterministic prediction baseline.

The contract is intentionally model-agnostic so future trained
models can replace the baseline without changing downstream
decision/simulation interfaces.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RevenuePrediction:
    customer_id: str
    payment_probability: float
    late_payment_risk: float
    expected_collection: float
    revenue_at_risk: float
    confidence: float
    evidence: tuple[str, ...]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def predict_customer_revenue(
    customer_id: str,
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> RevenuePrediction:
    """
    Generate a transparent customer-level revenue prediction.

    The prediction uses current observable financial signals only.
    It performs no mutation.
    """

    customer_invoices = [
        invoice
        for invoice in invoices
        if str(invoice.get("customer_id", "")) == str(customer_id)
    ]

    customer_payments = [
        payment
        for payment in payments
        if str(payment.get("customer_id", "")) == str(customer_id)
    ]

    total_invoiced = sum(
        float(invoice.get("amount", 0) or 0)
        for invoice in customer_invoices
    )

    outstanding = sum(
        float(
            invoice.get(
                "outstanding_amount",
                invoice.get("balance", 0),
            )
            or 0
        )
        for invoice in customer_invoices
    )

    overdue_amount = sum(
        float(
            invoice.get(
                "outstanding_amount",
                invoice.get("balance", 0),
            )
            or 0
        )
        for invoice in customer_invoices
        if int(invoice.get("days_overdue", 0) or 0) > 30
    )

    overdue_count = sum(
        1
        for invoice in customer_invoices
        if (
            float(
                invoice.get(
                    "outstanding_amount",
                    invoice.get("balance", 0),
                )
                or 0
            )
            > 0
            and int(invoice.get("days_overdue", 0) or 0) > 30
        )
    )

    total_paid = sum(
        float(payment.get("amount", 0) or 0)
        for payment in customer_payments
    )

    if total_invoiced <= 0:
        return RevenuePrediction(
            customer_id=str(customer_id),
            payment_probability=0.0,
            late_payment_risk=0.0,
            expected_collection=0.0,
            revenue_at_risk=0.0,
            confidence=0.0,
            evidence=("No invoiced revenue available.",),
        )

    collection_rate = _clamp(
        (total_invoiced - outstanding) / total_invoiced
    )

    outstanding_ratio = _clamp(
        outstanding / total_invoiced
    )

    overdue_ratio = _clamp(
        overdue_amount / total_invoiced
    )

    # Transparent baseline:
    # strong collection history increases payment probability;
    # outstanding and overdue exposure decrease it.
    payment_probability = _clamp(
        0.50
        + (collection_rate * 0.35)
        - (outstanding_ratio * 0.20)
        - (overdue_ratio * 0.25)
    )

    late_payment_risk = _clamp(
        (outstanding_ratio * 0.45)
        + (overdue_ratio * 0.40)
        + min(0.15, overdue_count * 0.05)
    )

    expected_collection = outstanding * payment_probability

    revenue_at_risk = max(
        0.0,
        outstanding - expected_collection,
    )

    evidence: list[str] = [
        f"collection_rate={collection_rate:.4f}",
        f"outstanding_ratio={outstanding_ratio:.4f}",
        f"overdue_ratio={overdue_ratio:.4f}",
    ]

    if overdue_count:
        evidence.append(
            f"overdue_invoice_count={overdue_count}"
        )

    if customer_payments:
        evidence.append(
            f"payment_count={len(customer_payments)}"
        )

    confidence = _clamp(
        0.45
        + min(0.25, len(customer_invoices) * 0.05)
        + min(0.15, len(customer_payments) * 0.05)
    )

    return RevenuePrediction(
        customer_id=str(customer_id),
        payment_probability=payment_probability,
        late_payment_risk=late_payment_risk,
        expected_collection=expected_collection,
        revenue_at_risk=revenue_at_risk,
        confidence=confidence,
        evidence=tuple(evidence),
    )


def predict_all_customers(
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> tuple[RevenuePrediction, ...]:
    """Generate predictions for every known customer."""

    customer_ids = {
        str(invoice["customer_id"])
        for invoice in invoices
        if invoice.get("customer_id") is not None
    }

    customer_ids.update(
        str(payment["customer_id"])
        for payment in payments
        if payment.get("customer_id") is not None
    )

    return tuple(
        predict_customer_revenue(
            customer_id,
            invoices,
            payments,
        )
        for customer_id in sorted(customer_ids)
    )
