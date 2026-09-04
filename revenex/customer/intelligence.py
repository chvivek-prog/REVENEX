"""
REVENEX Stage 32 — Customer Intelligence.

Builds a deterministic Customer 360 intelligence profile from
revenue state. This layer is read-only and has no provider or
financial side effects.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CustomerProfile:
    customer_id: str
    invoice_count: int
    payment_count: int
    total_invoiced: float
    total_paid: float
    outstanding: float
    overdue_amount: float
    overdue_invoice_count: int
    collection_rate: float
    risk_score: float
    health: str
    reasons: tuple[str, ...]


def _money(value: Any) -> float:
    return float(value or 0)


def build_customer_profile(
    customer_id: str,
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> CustomerProfile:
    """
    Build a customer-level revenue intelligence profile.

    All calculations are deterministic and read-only.
    """

    customer_invoices = [
        invoice
        for invoice in invoices
        if str(
            invoice.get("customer_id", "")
        ) == str(customer_id)
    ]

    customer_payments = [
        payment
        for payment in payments
        if str(
            payment.get("customer_id", "")
        ) == str(customer_id)
    ]

    total_invoiced = sum(
        _money(invoice.get("amount"))
        for invoice in customer_invoices
    )

    outstanding = sum(
        _money(
            invoice.get(
                "outstanding_amount",
                invoice.get("balance", 0),
            )
        )
        for invoice in customer_invoices
    )

    overdue_invoices = [
        invoice
        for invoice in customer_invoices
        if _money(
            invoice.get(
                "outstanding_amount",
                invoice.get("balance", 0),
            )
        ) > 0
        and int(invoice.get("days_overdue", 0) or 0) > 30
    ]

    overdue_amount = sum(
        _money(
            invoice.get(
                "outstanding_amount",
                invoice.get("balance", 0),
            )
        )
        for invoice in overdue_invoices
    )

    total_paid = sum(
        _money(payment.get("amount"))
        for payment in customer_payments
    )

    collection_rate = (
        max(
            0.0,
            min(
                1.0,
                (total_invoiced - outstanding)
                / total_invoiced,
            ),
        )
        if total_invoiced > 0
        else 0.0
    )

    reasons: list[str] = []

    if overdue_amount > 0:
        reasons.append(
            "Customer has overdue outstanding exposure."
        )

    if overdue_invoices:
        reasons.append(
            f"{len(overdue_invoices)} invoice(s) are more than "
            "30 days overdue."
        )

    if collection_rate < 0.50 and total_invoiced > 0:
        reasons.append(
            "Collection rate is below 50%."
        )

    risk_score = 0.0

    if overdue_amount > 0:
        risk_score += 0.35

    if overdue_invoices:
        risk_score += min(
            0.30,
            len(overdue_invoices) * 0.10,
        )

    if total_invoiced > 0 and collection_rate < 0.50:
        risk_score += 0.20

    if outstanding > 0 and total_invoiced > 0:
        exposure_ratio = outstanding / total_invoiced
        risk_score += min(
            0.15,
            exposure_ratio * 0.15,
        )

    risk_score = min(1.0, risk_score)

    if risk_score >= 0.75:
        health = "CRITICAL"
    elif risk_score >= 0.55:
        health = "AT_RISK"
    elif risk_score >= 0.30:
        health = "WATCH"
    else:
        health = "HEALTHY"

    return CustomerProfile(
        customer_id=str(customer_id),
        invoice_count=len(customer_invoices),
        payment_count=len(customer_payments),
        total_invoiced=total_invoiced,
        total_paid=total_paid,
        outstanding=outstanding,
        overdue_amount=overdue_amount,
        overdue_invoice_count=len(overdue_invoices),
        collection_rate=collection_rate,
        risk_score=risk_score,
        health=health,
        reasons=tuple(reasons),
    )


def build_customer_profiles(
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> tuple[CustomerProfile, ...]:
    """
    Build profiles for every customer represented in invoices
    or payments.
    """

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
        build_customer_profile(
            customer_id,
            invoices,
            payments,
        )
        for customer_id in sorted(customer_ids)
    )
