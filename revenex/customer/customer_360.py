"""
REVENEX Stage 33 — Customer 360.

Combines customer-level financial and behavioural signals into
one deterministic, read-only intelligence view.
"""

from dataclasses import dataclass
from typing import Any

from revenex.customer.intelligence import (
    CustomerProfile,
    build_customer_profile,
)


@dataclass(frozen=True)
class Customer360:
    customer_id: str

    financial: CustomerProfile

    revenue_share: float
    average_invoice_value: float
    average_payment_value: float

    overdue_ratio: float
    outstanding_ratio: float

    attention_level: str
    attention_reasons: tuple[str, ...]

    recommended_focus: str


def build_customer_360(
    customer_id: str,
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> Customer360:
    """Build a complete read-only customer intelligence view."""

    profile = build_customer_profile(
        customer_id,
        invoices,
        payments,
    )

    total_revenue = sum(
        float(invoice.get("amount", 0) or 0)
        for invoice in invoices
    )

    revenue_share = (
        profile.total_invoiced / total_revenue
        if total_revenue > 0
        else 0.0
    )

    average_invoice_value = (
        profile.total_invoiced / profile.invoice_count
        if profile.invoice_count
        else 0.0
    )

    average_payment_value = (
        profile.total_paid / profile.payment_count
        if profile.payment_count
        else 0.0
    )

    overdue_ratio = (
        profile.overdue_invoice_count / profile.invoice_count
        if profile.invoice_count
        else 0.0
    )

    outstanding_ratio = (
        profile.outstanding / profile.total_invoiced
        if profile.total_invoiced > 0
        else 0.0
    )

    reasons = list(profile.reasons)

    if revenue_share >= 0.25:
        reasons.append(
            "Customer represents a material share of invoiced revenue."
        )

    if outstanding_ratio >= 0.50:
        reasons.append(
            "More than half of the customer's invoiced value remains outstanding."
        )

    if overdue_ratio >= 0.50:
        reasons.append(
            "At least half of the customer's invoices are materially overdue."
        )

    if profile.health == "CRITICAL":
        attention_level = "CRITICAL"
    elif profile.health == "AT_RISK":
        attention_level = "HIGH"
    elif reasons:
        attention_level = "MEDIUM"
    else:
        attention_level = "LOW"

    if profile.overdue_amount > 0:
        recommended_focus = "RECOVERY"
    elif profile.outstanding > 0:
        recommended_focus = "COLLECTION"
    elif revenue_share >= 0.25:
        recommended_focus = "CUSTOMER_HEALTH"
    else:
        recommended_focus = "MONITOR"

    return Customer360(
        customer_id=str(customer_id),
        financial=profile,
        revenue_share=revenue_share,
        average_invoice_value=average_invoice_value,
        average_payment_value=average_payment_value,
        overdue_ratio=overdue_ratio,
        outstanding_ratio=outstanding_ratio,
        attention_level=attention_level,
        attention_reasons=tuple(reasons),
        recommended_focus=recommended_focus,
    )


def build_customer_360_views(
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> tuple[Customer360, ...]:
    """Build Customer 360 views for every known customer."""

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
        build_customer_360(
            customer_id,
            invoices,
            payments,
        )
        for customer_id in sorted(customer_ids)
    )
