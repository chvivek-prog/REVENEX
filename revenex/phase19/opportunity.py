from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class OpportunityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class RevenueOpportunity:
    opportunity_id: str
    entity_id: str
    exposure: float
    expected_recovery: float
    remaining_exposure: float
    confidence: float
    urgency: float
    evidence_quality: float
    opportunity_score: float
    opportunity_level: OpportunityLevel
    recommended_focus: str
    explanation: str
    evidence_refs: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class OpportunityReport:
    opportunities: tuple[RevenueOpportunity, ...]
    total_opportunities: int
    total_exposure: float
    total_expected_recovery: float
    total_remaining_exposure: float
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _ratio(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0

    if value > 1:
        value /= 100.0

    return max(0.0, min(1.0, value))


def _impact_level(score: float) -> OpportunityLevel:
    if score >= 0.90:
        return OpportunityLevel.CRITICAL
    if score >= 0.65:
        return OpportunityLevel.HIGH
    if score >= 0.35:
        return OpportunityLevel.MEDIUM
    return OpportunityLevel.LOW


def _focus(level: OpportunityLevel) -> str:
    return {
        OpportunityLevel.CRITICAL: "IMMEDIATE_REVIEW",
        OpportunityLevel.HIGH: "PRIORITY_REVIEW",
        OpportunityLevel.MEDIUM: "MONITOR",
        OpportunityLevel.LOW: "ROUTINE_REVIEW",
    }[level]


def detect_revenue_opportunities(
    records: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> OpportunityReport:
    opportunities: list[RevenueOpportunity] = []

    for index, record in enumerate(records, start=1):
        entity_id = str(
            record.get("entity_id")
            or record.get("customer_id")
            or record.get("invoice_id")
            or f"entity-{index}"
        )

        exposure = max(
            0.0,
            float(
                record.get("exposure")
                or record.get("outstanding")
                or record.get("outstanding_amount")
                or 0
            ),
        )

        expected_recovery = max(
            0.0,
            float(
                record.get("expected_recovery")
                or record.get("expected_collection")
                or record.get("recovery")
                or 0
            ),
        )

        expected_recovery = min(expected_recovery, exposure)

        remaining = max(0.0, exposure - expected_recovery)

        confidence = _ratio(
            record.get("confidence")
            or record.get("prediction_confidence")
        )

        urgency = _ratio(
            record.get("urgency")
            or record.get("risk_urgency")
        )

        evidence_quality = _ratio(
            record.get("evidence_quality")
            or record.get("evidence_score")
        )

        recovery_ratio = (
            expected_recovery / exposure
            if exposure > 0
            else 0.0
        )

        remaining_ratio = (
            remaining / exposure
            if exposure > 0
            else 0.0
        )

        score = round(
            min(
                1.0,
                (
                    0.30 * recovery_ratio
                    + 0.25 * remaining_ratio
                    + 0.20 * urgency
                    + 0.15 * confidence
                    + 0.10 * evidence_quality
                ),
            ),
            4,
        )

        level = _impact_level(score)

        explanation = (
            f"{entity_id} represents ₹{exposure:,.2f} exposure, "
            f"with ₹{expected_recovery:,.2f} expected recovery and "
            f"₹{remaining:,.2f} remaining exposure. "
            f"Opportunity score is {score:.2f}. "
            f"Recommendation is advisory and requires human review."
        )

        opportunities.append(
            RevenueOpportunity(
                opportunity_id=f"OPP19-{index:04d}",
                entity_id=entity_id,
                exposure=exposure,
                expected_recovery=expected_recovery,
                remaining_exposure=remaining,
                confidence=confidence,
                urgency=urgency,
                evidence_quality=evidence_quality,
                opportunity_score=score,
                opportunity_level=level,
                recommended_focus=_focus(level),
                explanation=explanation,
                evidence_refs=(
                    f"entity:{entity_id}",
                    "exposure",
                    "expected_recovery",
                    "remaining_exposure",
                    "confidence",
                    "urgency",
                    "evidence_quality",
                ),
            )
        )

    opportunities.sort(
        key=lambda item: (
            -item.opportunity_score,
            -item.remaining_exposure,
            item.entity_id,
        )
    )

    return OpportunityReport(
        opportunities=tuple(opportunities),
        total_opportunities=len(opportunities),
        total_exposure=round(
            sum(item.exposure for item in opportunities), 2
        ),
        total_expected_recovery=round(
            sum(item.expected_recovery for item in opportunities), 2
        ),
        total_remaining_exposure=round(
            sum(item.remaining_exposure for item in opportunities), 2
        ),
    )
