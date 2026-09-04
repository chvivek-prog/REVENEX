from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ImpactLevel(str, Enum):
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

    impact_score: float
    impact_level: ImpactLevel

    recommended_focus: str
    explanation: str
    evidence_refs: tuple[str, ...]

    read_only: bool = True
    human_review_required: bool = True


@dataclass(frozen=True)
class PrioritizationReport:
    opportunities: tuple[RevenueOpportunity, ...]

    opportunities_analyzed: int
    critical_count: int
    high_count: int

    total_exposure: float
    total_expected_recovery: float
    total_remaining_exposure: float

    highest_priority_id: str | None
    highest_priority_score: float

    prioritization_summary: str

    read_only: bool = True
    human_review_required: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return max(0.0, round(float(value or 0), 2))
    except (TypeError, ValueError):
        return 0.0


def _ratio(value: Any) -> float:
    try:
        return min(max(float(value), 0.0), 1.0)
    except (TypeError, ValueError):
        return 0.0


def _impact_level(score: float) -> ImpactLevel:
    score = float(score)

    if score >= 0.90:
        return ImpactLevel.CRITICAL

    if score >= 0.50:
        return ImpactLevel.HIGH

    if score >= 0.25:
        return ImpactLevel.MEDIUM

    return ImpactLevel.LOW


def _focus(level: ImpactLevel) -> str:
    if level == ImpactLevel.CRITICAL:
        return "IMMEDIATE_REVIEW"
    if level == ImpactLevel.HIGH:
        return "PRIORITY_REVIEW"
    if level == ImpactLevel.MEDIUM:
        return "SCHEDULED_REVIEW"
    return "MONITOR"


def prioritize_revenue_impact(
    records: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> PrioritizationReport:

    opportunities: list[RevenueOpportunity] = []

    for index, record in enumerate(records, start=1):
        entity_id = str(
            record.get("entity_id")
            or record.get("customer_id")
            or record.get("invoice_id")
            or f"entity-{index}"
        )

        exposure = _money(
            record.get("exposure")
            or record.get("outstanding")
            or record.get("invoice_amount")
        )

        expected_recovery = min(
            exposure,
            _money(
                record.get("expected_recovery")
                or record.get("expected_collection")
                or record.get("selected_expected_collection")
            ),
        )

        remaining = round(
            max(exposure - expected_recovery, 0.0),
            2,
        )

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

        recovery_value_ratio = (
            expected_recovery / exposure
            if exposure > 0
            else 0.0
        )

        exposure_ratio = (
            remaining / exposure
            if exposure > 0
            else 0.0
        )

        # Deterministic prioritization:
        # remaining exposure + recoverable value + urgency
        # + confidence/evidence quality.
        #
        # Remaining exposure is intentionally rewarded because
        # the purpose of this score is to identify revenue that
        # deserves attention. A fully recoverable opportunity
        # can therefore still be CRITICAL when urgency,
        # confidence and evidence are all maximal.
        score = round(
            min(
                1.0,
                (
                    0.30 * recovery_value_ratio
                    + 0.30 * urgency
                    + 0.20 * confidence
                    + 0.20 * evidence_quality
                ),
            ),
            4,
        )

        level = _impact_level(score)

        if remaining > 0:
            explanation = (
                f"{entity_id} has ₹{remaining:,.2f} remaining exposure "
                f"after expected recovery of ₹{expected_recovery:,.2f}. "
                f"Impact score is {score:.2f}."
            )
        else:
            explanation = (
                f"{entity_id} has no remaining projected exposure. "
                f"Impact score is {score:.2f}."
            )

        opportunities.append(
            RevenueOpportunity(
                opportunity_id=f"OPP-{index:04d}",
                entity_id=entity_id,
                exposure=exposure,
                expected_recovery=expected_recovery,
                remaining_exposure=remaining,
                confidence=confidence,
                urgency=urgency,
                evidence_quality=evidence_quality,
                impact_score=score,
                impact_level=level,
                recommended_focus=_focus(level),
                explanation=explanation,
                evidence_refs=(
                    f"entity:{entity_id}",
                    "exposure",
                    "expected_recovery",
                    "confidence",
                    "urgency",
                    "evidence_quality",
                ),
            )
        )

    opportunities.sort(
        key=lambda item: (
            -item.impact_score,
            -item.remaining_exposure,
            -item.exposure,
            item.entity_id,
        )
    )

    total_exposure = round(
        sum(item.exposure for item in opportunities),
        2,
    )

    total_expected = round(
        sum(item.expected_recovery for item in opportunities),
        2,
    )

    total_remaining = round(
        sum(item.remaining_exposure for item in opportunities),
        2,
    )

    critical_count = sum(
        item.impact_level == ImpactLevel.CRITICAL
        for item in opportunities
    )

    high_count = sum(
        item.impact_level == ImpactLevel.HIGH
        for item in opportunities
    )

    highest = opportunities[0] if opportunities else None

    summary = (
        f"{len(opportunities)} revenue opportunity(s) were prioritized. "
        f"{critical_count} critical and {high_count} high-impact "
        f"opportunity(ies) require human review."
    )

    return PrioritizationReport(
        opportunities=tuple(opportunities),
        opportunities_analyzed=len(opportunities),
        critical_count=critical_count,
        high_count=high_count,
        total_exposure=total_exposure,
        total_expected_recovery=total_expected,
        total_remaining_exposure=total_remaining,
        highest_priority_id=(
            highest.opportunity_id if highest else None
        ),
        highest_priority_score=(
            highest.impact_score if highest else 0.0
        ),
        prioritization_summary=summary,
    )
