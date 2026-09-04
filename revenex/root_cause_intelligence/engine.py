from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RootCauseCategory(str, Enum):
    COLLECTION = "COLLECTION"
    PAYMENT = "PAYMENT"
    SETTLEMENT = "SETTLEMENT"
    CUSTOMER = "CUSTOMER"
    INVOICE = "INVOICE"
    SUBSCRIPTION = "SUBSCRIPTION"
    REFUND = "REFUND"
    DISPUTE = "DISPUTE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RootCause:
    cause_id: str
    category: RootCauseCategory
    title: str
    explanation: str
    affected_amount: float
    contribution: float
    confidence: float
    evidence: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class RootCauseReport:
    causes: tuple[RootCause, ...]
    total_causes: int
    primary_cause: RootCause | None
    affected_revenue: float
    average_confidence: float
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _cause(
    *,
    category: RootCauseCategory,
    title: str,
    explanation: str,
    amount: float,
    total_impact: float,
    confidence: float,
    evidence: tuple[str, ...],
) -> RootCause:
    contribution = (
        amount / total_impact
        if total_impact > 0
        else 0.0
    )

    return RootCause(
        cause_id=f"{category.value}:{title.upper().replace(' ', '_')}",
        category=category,
        title=title,
        explanation=explanation,
        affected_amount=amount,
        contribution=contribution,
        confidence=max(0.0, min(1.0, confidence)),
        evidence=evidence,
    )


def analyze_root_causes(
    *,
    expected_revenue: float | None = None,
    actual_revenue: float | None = None,
    unpaid_invoices: list[dict[str, Any]] | None = None,
    payment_failures: list[dict[str, Any]] | None = None,
    settlement_gaps: list[dict[str, Any]] | None = None,
    refunds: list[dict[str, Any]] | None = None,
    disputes: list[dict[str, Any]] | None = None,
    subscription_failures: list[dict[str, Any]] | None = None,
) -> tuple[RootCause, ...]:
    unpaid_invoices = unpaid_invoices or []
    payment_failures = payment_failures or []
    settlement_gaps = settlement_gaps or []
    refunds = refunds or []
    disputes = disputes or []
    subscription_failures = subscription_failures or []

    expected = _money(expected_revenue)
    actual = _money(actual_revenue)

    revenue_impact = max(expected - actual, 0.0)

    if revenue_impact <= 0:
        revenue_impact = sum(
            _money(x.get("amount"))
            for x in (
                unpaid_invoices
                + payment_failures
                + settlement_gaps
                + refunds
                + disputes
                + subscription_failures
            )
        )

    causes: list[RootCause] = []

    unpaid = sum(
        _money(x.get("amount", x.get("outstanding_amount")))
        for x in unpaid_invoices
    )

    if unpaid > 0:
        causes.append(
            _cause(
                category=RootCauseCategory.COLLECTION,
                title="Unpaid invoices",
                explanation=(
                    "Outstanding invoice exposure is contributing "
                    "to the observed revenue shortfall."
                ),
                amount=unpaid,
                total_impact=revenue_impact,
                confidence=0.90,
                evidence=(
                    f"unpaid_invoice_count={len(unpaid_invoices)}",
                    f"unpaid_amount={unpaid:.2f}",
                ),
            )
        )

    failed = sum(
        _money(x.get("amount"))
        for x in payment_failures
    )

    if failed > 0:
        causes.append(
            _cause(
                category=RootCauseCategory.PAYMENT,
                title="Payment failures",
                explanation=(
                    "Payment failures are reducing successful "
                    "revenue collection."
                ),
                amount=failed,
                total_impact=revenue_impact,
                confidence=0.88,
                evidence=(
                    f"payment_failure_count={len(payment_failures)}",
                    f"failed_payment_amount={failed:.2f}",
                ),
            )
        )

    gaps = sum(
        _money(x.get("amount", x.get("gap")))
        for x in settlement_gaps
    )

    if gaps > 0:
        causes.append(
            _cause(
                category=RootCauseCategory.SETTLEMENT,
                title="Settlement gaps",
                explanation=(
                    "Settlement shortfalls explain part of the "
                    "difference between expected and realized cash."
                ),
                amount=gaps,
                total_impact=revenue_impact,
                confidence=0.94,
                evidence=(
                    f"settlement_gap_count={len(settlement_gaps)}",
                    f"settlement_gap_amount={gaps:.2f}",
                ),
            )
        )

    refund_amount = sum(
        _money(x.get("amount"))
        for x in refunds
    )

    if refund_amount > 0:
        causes.append(
            _cause(
                category=RootCauseCategory.REFUND,
                title="Refund activity",
                explanation=(
                    "Refund activity is reducing realized revenue "
                    "relative to gross collections."
                ),
                amount=refund_amount,
                total_impact=revenue_impact,
                confidence=0.86,
                evidence=(
                    f"refund_count={len(refunds)}",
                    f"refund_amount={refund_amount:.2f}",
                ),
            )
        )

    dispute_amount = sum(
        _money(x.get("amount"))
        for x in disputes
    )

    if dispute_amount > 0:
        causes.append(
            _cause(
                category=RootCauseCategory.DISPUTE,
                title="Dispute exposure",
                explanation=(
                    "Disputed payment exposure is contributing "
                    "to revenue uncertainty."
                ),
                amount=dispute_amount,
                total_impact=revenue_impact,
                confidence=0.84,
                evidence=(
                    f"dispute_count={len(disputes)}",
                    f"dispute_amount={dispute_amount:.2f}",
                ),
            )
        )

    subscription_amount = sum(
        _money(x.get("amount"))
        for x in subscription_failures
    )

    if subscription_amount > 0:
        causes.append(
            _cause(
                category=RootCauseCategory.SUBSCRIPTION,
                title="Subscription failures",
                explanation=(
                    "Recurring payment or subscription failures "
                    "are reducing expected recurring revenue."
                ),
                amount=subscription_amount,
                total_impact=revenue_impact,
                confidence=0.87,
                evidence=(
                    f"subscription_failure_count="
                    f"{len(subscription_failures)}",
                    f"subscription_failure_amount="
                    f"{subscription_amount:.2f}",
                ),
            )
        )

    # If no direct evidence exists, explicitly report uncertainty
    # rather than inventing a root cause.
    if not causes and revenue_impact > 0:
        causes.append(
            _cause(
                category=RootCauseCategory.UNKNOWN,
                title="Insufficient evidence",
                explanation=(
                    "A revenue shortfall exists, but the supplied "
                    "evidence does not identify a reliable root cause."
                ),
                amount=revenue_impact,
                total_impact=revenue_impact,
                confidence=0.25,
                evidence=(
                    f"expected_revenue={expected:.2f}",
                    f"actual_revenue={actual:.2f}",
                    "direct_root_cause_evidence=0",
                ),
            )
        )

    return tuple(
        sorted(
            causes,
            key=lambda item: (
                item.affected_amount,
                item.confidence,
            ),
            reverse=True,
        )
    )


def summarize_root_causes(
    causes: list[RootCause] | tuple[RootCause, ...],
) -> RootCauseReport:
    items = tuple(causes)

    affected = sum(
        item.affected_amount
        for item in items
    )

    confidence = (
        sum(item.confidence for item in items) / len(items)
        if items
        else 0.0
    )

    return RootCauseReport(
        causes=items,
        total_causes=len(items),
        primary_cause=items[0] if items else None,
        affected_revenue=affected,
        average_confidence=confidence,
    )
