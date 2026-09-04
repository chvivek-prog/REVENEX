from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class InterventionType(str, Enum):
    RECOVERY_REVIEW = "RECOVERY_REVIEW"
    PAYMENT_FOLLOW_UP = "PAYMENT_FOLLOW_UP"
    RISK_REVIEW = "RISK_REVIEW"
    DATA_REVIEW = "DATA_REVIEW"
    MONITOR = "MONITOR"


class InterventionLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class RevenueIntervention:
    intervention_id: str
    entity_id: str
    intervention_type: InterventionType
    level: InterventionLevel
    exposure: float
    expected_recovery: float
    remaining_exposure: float
    confidence: float
    urgency: float
    evidence_quality: float
    intervention_score: float
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
class InterventionReport:
    interventions: tuple[RevenueIntervention, ...]
    total_interventions: int
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


def _level(score: float) -> InterventionLevel:
    if score >= 0.90:
        return InterventionLevel.CRITICAL
    if score >= 0.65:
        return InterventionLevel.HIGH
    if score >= 0.35:
        return InterventionLevel.MEDIUM
    return InterventionLevel.LOW


def _type(
    remaining: float,
    urgency: float,
    confidence: float,
    evidence_quality: float,
) -> InterventionType:
    if evidence_quality < 0.35:
        return InterventionType.DATA_REVIEW

    if remaining > 0 and urgency >= 0.70:
        return InterventionType.RECOVERY_REVIEW

    if remaining > 0 and confidence >= 0.60:
        return InterventionType.PAYMENT_FOLLOW_UP

    if urgency >= 0.50:
        return InterventionType.RISK_REVIEW

    return InterventionType.MONITOR


def _focus(level: InterventionLevel) -> str:
    return {
        InterventionLevel.CRITICAL: "IMMEDIATE_HUMAN_REVIEW",
        InterventionLevel.HIGH: "PRIORITY_HUMAN_REVIEW",
        InterventionLevel.MEDIUM: "SCHEDULED_REVIEW",
        InterventionLevel.LOW: "MONITOR",
    }[level]


def recommend_interventions(
    records: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> InterventionReport:
    interventions: list[RevenueIntervention] = []

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
                    0.25 * recovery_ratio
                    + 0.25 * remaining_ratio
                    + 0.25 * urgency
                    + 0.15 * confidence
                    + 0.10 * evidence_quality
                ),
            ),
            4,
        )

        level = _level(score)

        intervention_type = _type(
            remaining,
            urgency,
            confidence,
            evidence_quality,
        )

        explanation = (
            f"{entity_id} has ₹{exposure:,.2f} exposure, "
            f"₹{expected_recovery:,.2f} expected recovery and "
            f"₹{remaining:,.2f} remaining exposure. "
            f"Urgency is {urgency:.2f}, confidence is "
            f"{confidence:.2f}, and evidence quality is "
            f"{evidence_quality:.2f}. "
            f"REVENEX recommends {intervention_type.value} "
            f"for human review."
        )

        interventions.append(
            RevenueIntervention(
                intervention_id=f"INT20-{index:04d}",
                entity_id=entity_id,
                intervention_type=intervention_type,
                level=level,
                exposure=exposure,
                expected_recovery=expected_recovery,
                remaining_exposure=remaining,
                confidence=confidence,
                urgency=urgency,
                evidence_quality=evidence_quality,
                intervention_score=score,
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

    interventions.sort(
        key=lambda item: (
            -item.intervention_score,
            -item.remaining_exposure,
            item.entity_id,
        )
    )

    return InterventionReport(
        interventions=tuple(interventions),
        total_interventions=len(interventions),
        total_exposure=round(
            sum(item.exposure for item in interventions), 2
        ),
        total_expected_recovery=round(
            sum(item.expected_recovery for item in interventions), 2
        ),
        total_remaining_exposure=round(
            sum(item.remaining_exposure for item in interventions), 2
        ),
    )
