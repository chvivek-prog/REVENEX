from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CorrelationSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


@dataclass(frozen=True)
class CorrelationSignal:
    correlation_id: str
    entity_id: str

    invoice_amount: float
    payment_amount: float
    settlement_amount: float
    payout_amount: float

    collection_gap: float
    settlement_gap: float
    payout_gap: float

    correlation_score: float
    severity: CorrelationSeverity

    signal: str
    explanation: str
    evidence_refs: tuple[str, ...]

    human_review_required: bool = True
    read_only: bool = True


@dataclass(frozen=True)
class CorrelationReport:
    signals: tuple[CorrelationSignal, ...]

    entities_analyzed: int
    correlated_entities: int
    high_risk_correlations: int

    total_collection_gap: float
    total_settlement_gap: float
    total_payout_gap: float

    average_correlation_score: float
    summary: str

    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return max(0.0, round(float(value or 0), 2))
    except (TypeError, ValueError):
        return 0.0


def _score(
    collection_gap: float,
    settlement_gap: float,
    payout_gap: float,
    invoice_amount: float,
) -> float:
    if invoice_amount <= 0:
        return 0.0

    total_gap = (
        collection_gap
        + settlement_gap
        + payout_gap
    )

    return round(
        min(
            1.0,
            total_gap / invoice_amount,
        ),
        4,
    )


def _severity(score: float) -> CorrelationSeverity:
    if score >= 0.50:
        return CorrelationSeverity.CRITICAL
    if score >= 0.25:
        return CorrelationSeverity.HIGH
    if score >= 0.10:
        return CorrelationSeverity.MEDIUM
    if score > 0:
        return CorrelationSeverity.LOW
    return CorrelationSeverity.NONE


def correlate_revenue_systems(
    records: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> CorrelationReport:

    signals: list[CorrelationSignal] = []

    for index, record in enumerate(records, start=1):
        entity_id = str(
            record.get("entity_id")
            or record.get("customer_id")
            or record.get("invoice_id")
            or f"entity-{index}"
        )

        invoice_amount = _money(
            record.get("invoice_amount")
            or record.get("invoice")
            or record.get("expected_amount")
        )

        payment_amount = _money(
            record.get("payment_amount")
            or record.get("collected_amount")
            or record.get("payment")
        )

        settlement_amount = _money(
            record.get("settlement_amount")
            or record.get("settled_amount")
            or record.get("settlement")
        )

        payout_amount = _money(
            record.get("payout_amount")
            or record.get("payout")
        )

        collection_gap = round(
            max(invoice_amount - payment_amount, 0.0),
            2,
        )

        settlement_gap = round(
            max(payment_amount - settlement_amount, 0.0),
            2,
        )

        payout_gap = round(
            max(settlement_amount - payout_amount, 0.0),
            2,
        )

        score = _score(
            collection_gap,
            settlement_gap,
            payout_gap,
            invoice_amount,
        )

        severity = _severity(score)

        if collection_gap > 0:
            signal = "CROSS_SYSTEM_COLLECTION_GAP"
            explanation = (
                "Invoice exposure is not fully represented "
                "by observed payment activity."
            )
        elif settlement_gap > 0:
            signal = "CROSS_SYSTEM_SETTLEMENT_GAP"
            explanation = (
                "Observed payment value exceeds the settlement "
                "value currently represented."
            )
        elif payout_gap > 0:
            signal = "CROSS_SYSTEM_PAYOUT_GAP"
            explanation = (
                "Observed settlement value exceeds the payout "
                "value currently represented."
            )
        else:
            signal = "CROSS_SYSTEM_ALIGNED"
            explanation = (
                "Invoice, payment, settlement, and payout "
                "values are aligned within the supplied data."
            )

        if score > 0:
            signals.append(
                CorrelationSignal(
                    correlation_id=f"CORR-{index:04d}",
                    entity_id=entity_id,
                    invoice_amount=invoice_amount,
                    payment_amount=payment_amount,
                    settlement_amount=settlement_amount,
                    payout_amount=payout_amount,
                    collection_gap=collection_gap,
                    settlement_gap=settlement_gap,
                    payout_gap=payout_gap,
                    correlation_score=score,
                    severity=severity,
                    signal=signal,
                    explanation=explanation,
                    evidence_refs=(
                        f"entity:{entity_id}",
                        "invoice_amount",
                        "payment_amount",
                        "settlement_amount",
                        "payout_amount",
                    ),
                )
            )

    signals.sort(
        key=lambda item: (
            -item.correlation_score,
            -item.collection_gap,
            -item.settlement_gap,
            -item.payout_gap,
            item.entity_id,
        )
    )

    total_collection_gap = round(
        sum(item.collection_gap for item in signals),
        2,
    )

    total_settlement_gap = round(
        sum(item.settlement_gap for item in signals),
        2,
    )

    total_payout_gap = round(
        sum(item.payout_gap for item in signals),
        2,
    )

    high_risk = sum(
        item.severity
        in {
            CorrelationSeverity.CRITICAL,
            CorrelationSeverity.HIGH,
        }
        for item in signals
    )

    average_score = round(
        (
            sum(item.correlation_score for item in signals)
            / len(signals)
        )
        if signals
        else 0.0,
        4,
    )

    summary = (
        f"{len(signals)} cross-system correlation signal(s) "
        f"identified across {len(records)} entity record(s). "
        f"{high_risk} high-risk correlation(s) require human review."
    )

    return CorrelationReport(
        signals=tuple(signals),
        entities_analyzed=len(records),
        correlated_entities=len(signals),
        high_risk_correlations=high_risk,
        total_collection_gap=total_collection_gap,
        total_settlement_gap=total_settlement_gap,
        total_payout_gap=total_payout_gap,
        average_correlation_score=average_score,
        summary=summary,
    )
