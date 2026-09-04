"""REVENEX Phase 27 — Root Cause Intelligence.

Connects revenue anomalies to lifecycle evidence and produces
deterministic, explainable root-cause findings.

This module is strictly read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RootCauseCategory(str, Enum):
    PAYMENT = "PAYMENT"
    SETTLEMENT = "SETTLEMENT"
    REFUND = "REFUND"
    DISPUTE = "DISPUTE"
    INVOICE = "INVOICE"
    ORDER = "ORDER"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RootCauseFinding:
    finding_id: str
    category: RootCauseCategory
    entity_type: str
    entity_id: str
    confidence: float
    exposure: float
    explanation: str
    evidence: tuple[str, ...]
    contributing_factors: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class RootCauseReport:
    findings: tuple[RootCauseFinding, ...]
    total_findings: int
    total_exposure: float
    high_confidence_count: int
    human_review_required: bool
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _confidence(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _finding(
    *,
    category: RootCauseCategory,
    entity_type: str,
    entity_id: str,
    exposure: float,
    confidence: float,
    explanation: str,
    evidence: tuple[str, ...],
    factors: tuple[str, ...],
) -> RootCauseFinding:
    return RootCauseFinding(
        finding_id=(
            f"{category.value}:{entity_type}:{entity_id}"
        ),
        category=category,
        entity_type=entity_type,
        entity_id=entity_id,
        confidence=_confidence(confidence),
        exposure=max(0.0, exposure),
        explanation=explanation,
        evidence=evidence,
        contributing_factors=factors,
    )


def analyze_root_causes(
    *,
    anomalies: list[dict[str, Any]]
    | tuple[dict[str, Any], ...]
    | None = None,
    invoices: list[dict[str, Any]] | None = None,
    payments: list[dict[str, Any]] | None = None,
    settlements: list[dict[str, Any]] | None = None,
    refunds: list[dict[str, Any]] | None = None,
    disputes: list[dict[str, Any]] | None = None,
    orders: list[dict[str, Any]] | None = None,
) -> tuple[RootCauseFinding, ...]:
    """Determine deterministic root causes from supplied evidence.

    The engine never executes actions and never mutates financial
    or provider state.
    """

    anomalies = tuple(anomalies or [])
    invoices = invoices or []
    payments = payments or []
    settlements = settlements or []
    refunds = refunds or []
    disputes = disputes or []
    orders = orders or []

    findings: list[RootCauseFinding] = []

    invoices_by_id = {
        str(
            invoice.get(
                "invoice_id",
                invoice.get("id", ""),
            )
        ): invoice
        for invoice in invoices
    }

    payments_by_id = {
        str(
            payment.get(
                "payment_id",
                payment.get("id", ""),
            )
        ): payment
        for payment in payments
    }

    settlements_by_payment: dict[str, float] = {}

    for settlement in settlements:
        payment_id = settlement.get("payment_id")

        if not payment_id:
            continue

        key = str(payment_id)

        settlements_by_payment[key] = (
            settlements_by_payment.get(key, 0.0)
            + _money(settlement.get("amount"))
        )

    refunds_by_payment: dict[str, float] = {}

    for refund in refunds:
        payment_id = refund.get("payment_id")

        if not payment_id:
            continue

        key = str(payment_id)

        refunds_by_payment[key] = (
            refunds_by_payment.get(key, 0.0)
            + _money(refund.get("amount"))
        )

    disputes_by_payment: dict[str, float] = {}

    for dispute in disputes:
        payment_id = dispute.get("payment_id")

        if not payment_id:
            continue

        key = str(payment_id)

        disputes_by_payment[key] = (
            disputes_by_payment.get(key, 0.0)
            + _money(dispute.get("amount"))
        )

    for anomaly in anomalies:
        anomaly_type = str(
            anomaly.get(
                "anomaly_type",
                anomaly.get("type", ""),
            )
        ).upper()

        entity_type = str(
            anomaly.get("entity_type", "")
        ).lower()

        entity_id = str(
            anomaly.get("entity_id", "")
        )

        exposure = abs(
            _money(
                anomaly.get(
                    "exposure",
                    anomaly.get(
                        "variance",
                        anomaly.get("amount", 0),
                    ),
                )
            )
        )

        if not entity_id:
            continue

        if (
            "SETTLEMENT" in anomaly_type
            or entity_type == "settlement"
        ):
            settlement = next(
                (
                    item
                    for item in settlements
                    if str(
                        item.get(
                            "settlement_id",
                            item.get("id", ""),
                        )
                    )
                    == entity_id
                ),
                None,
            )

            payment_id = (
                str(
                    settlement.get("payment_id")
                )
                if settlement
                and settlement.get("payment_id")
                else None
            )

            payment_amount = (
                _money(
                    payments_by_id.get(
                        payment_id,
                        {},
                    ).get("amount")
                )
                if payment_id
                else 0.0
            )

            settled_amount = (
                settlements_by_payment.get(
                    payment_id,
                    0.0,
                )
                if payment_id
                else _money(
                    settlement.get("amount")
                )
                if settlement
                else 0.0
            )

            gap = max(
                payment_amount - settled_amount,
                exposure,
                0.0,
            )

            findings.append(
                _finding(
                    category=RootCauseCategory.SETTLEMENT,
                    entity_type="settlement",
                    entity_id=entity_id,
                    exposure=gap,
                    confidence=0.95,
                    explanation=(
                        "Settlement evidence indicates a "
                        "shortfall against the connected "
                        "payment lifecycle."
                    ),
                    evidence=(
                        f"settlement={entity_id}",
                        f"payment={payment_id or 'UNKNOWN'}",
                        f"payment_amount={payment_amount:.2f}",
                        f"settled_amount={settled_amount:.2f}",
                        f"gap={gap:.2f}",
                    ),
                    factors=(
                        "settlement_shortfall",
                        "payment_settlement_variance",
                    ),
                )
            )
            continue

        if (
            "REFUND" in anomaly_type
            or entity_type == "refund"
        ):
            refund = next(
                (
                    item
                    for item in refunds
                    if str(
                        item.get(
                            "refund_id",
                            item.get("id", ""),
                        )
                    )
                    == entity_id
                ),
                None,
            )

            payment_id = (
                str(
                    refund.get("payment_id")
                )
                if refund
                and refund.get("payment_id")
                else None
            )

            payment_amount = (
                _money(
                    payments_by_id.get(
                        payment_id,
                        {},
                    ).get("amount")
                )
                if payment_id
                else 0.0
            )

            refund_amount = (
                _money(
                    refund.get("amount")
                )
                if refund
                else exposure
            )

            confidence = (
                0.95
                if payment_id
                and payment_amount > 0
                else 0.75
            )

            findings.append(
                _finding(
                    category=RootCauseCategory.REFUND,
                    entity_type="refund",
                    entity_id=entity_id,
                    exposure=refund_amount,
                    confidence=confidence,
                    explanation=(
                        "Refund activity is a direct "
                        "contributor to the observed "
                        "revenue anomaly."
                    ),
                    evidence=(
                        f"refund={entity_id}",
                        f"payment={payment_id or 'UNKNOWN'}",
                        f"refund_amount={refund_amount:.2f}",
                        f"payment_amount={payment_amount:.2f}",
                    ),
                    factors=(
                        "refund_activity",
                        "revenue_reversal",
                    ),
                )
            )
            continue

        if (
            "DISPUTE" in anomaly_type
            or entity_type == "dispute"
        ):
            dispute = next(
                (
                    item
                    for item in disputes
                    if str(
                        item.get(
                            "dispute_id",
                            item.get("id", ""),
                        )
                    )
                    == entity_id
                ),
                None,
            )

            amount = (
                _money(
                    dispute.get("amount")
                )
                if dispute
                else exposure
            )

            findings.append(
                _finding(
                    category=RootCauseCategory.DISPUTE,
                    entity_type="dispute",
                    entity_id=entity_id,
                    exposure=amount,
                    confidence=0.95,
                    explanation=(
                        "Dispute activity is a direct "
                        "contributor to revenue exposure."
                    ),
                    evidence=(
                        f"dispute={entity_id}",
                        f"amount={amount:.2f}",
                    ),
                    factors=(
                        "dispute_activity",
                        "revenue_at_risk",
                    ),
                )
            )
            continue

        if (
            "PAYMENT" in anomaly_type
            or entity_type == "payment"
        ):
            payment = payments_by_id.get(
                entity_id
            )

            amount = (
                _money(
                    payment.get("amount")
                )
                if payment
                else exposure
            )

            factors = [
                "payment_anomaly"
            ]

            if entity_id in settlements_by_payment:
                factors.append(
                    "settlement_link_present"
                )

            if entity_id in refunds_by_payment:
                factors.append(
                    "refund_link_present"
                )

            if entity_id in disputes_by_payment:
                factors.append(
                    "dispute_link_present"
                )

            findings.append(
                _finding(
                    category=RootCauseCategory.PAYMENT,
                    entity_type="payment",
                    entity_id=entity_id,
                    exposure=amount,
                    confidence=(
                        0.90
                        if payment
                        else 0.70
                    ),
                    explanation=(
                        "Payment behavior is the primary "
                        "observable contributor to the "
                        "detected revenue anomaly."
                    ),
                    evidence=(
                        f"payment={entity_id}",
                        f"amount={amount:.2f}",
                    ),
                    factors=tuple(factors),
                )
            )
            continue

        if (
            "INVOICE" in anomaly_type
            or entity_type == "invoice"
        ):
            invoice = invoices_by_id.get(
                entity_id
            )

            outstanding = (
                _money(
                    invoice.get(
                        "outstanding_amount",
                        invoice.get(
                            "amount_due",
                            0,
                        ),
                    )
                )
                if invoice
                else exposure
            )

            findings.append(
                _finding(
                    category=RootCauseCategory.INVOICE,
                    entity_type="invoice",
                    entity_id=entity_id,
                    exposure=outstanding,
                    confidence=0.90 if invoice else 0.70,
                    explanation=(
                        "Invoice exposure is a direct "
                        "contributor to the revenue issue."
                    ),
                    evidence=(
                        f"invoice={entity_id}",
                        f"outstanding={outstanding:.2f}",
                    ),
                    factors=(
                        "invoice_exposure",
                        "collection_gap",
                    ),
                )
            )
            continue

        findings.append(
            _finding(
                category=RootCauseCategory.UNKNOWN,
                entity_type=entity_type or "unknown",
                entity_id=entity_id,
                exposure=exposure,
                confidence=0.50,
                explanation=(
                    "The supplied anomaly does not contain "
                    "enough lifecycle evidence to establish "
                    "a more specific root cause."
                ),
                evidence=(
                    f"anomaly_type={anomaly_type or 'UNKNOWN'}",
                    f"entity={entity_id}",
                ),
                factors=(
                    "insufficient_root_cause_evidence",
                ),
            )
        )

    return tuple(findings)


def summarize_root_causes(
    findings: list[RootCauseFinding]
    | tuple[RootCauseFinding, ...],
) -> RootCauseReport:
    findings = tuple(findings)

    high_confidence = sum(
        1
        for finding in findings
        if finding.confidence >= 0.80
    )

    return RootCauseReport(
        findings=findings,
        total_findings=len(findings),
        total_exposure=sum(
            finding.exposure
            for finding in findings
        ),
        high_confidence_count=high_confidence,
        human_review_required=bool(findings),
        read_only=True,
        financial_mutation=False,
        provider_mutation=False,
    )
