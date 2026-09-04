from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PropagationLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class RiskDependency:
    source_id: str
    target_id: str
    relationship: str
    propagated_exposure: float
    evidence_ref: str


@dataclass(frozen=True)
class RiskPropagation:
    entity_id: str
    direct_exposure: float
    remaining_exposure: float
    concentration_ratio: float
    propagated_exposure: float
    propagation_score: float
    propagation_level: PropagationLevel
    dependencies: tuple[RiskDependency, ...]
    risk_path: tuple[str, ...]
    explanation: str
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class RiskPropagationReport:
    propagations: tuple[RiskPropagation, ...]
    total_direct_exposure: float
    total_remaining_exposure: float
    total_propagated_exposure: float
    highest_concentration: float
    critical_count: int
    high_count: int
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


def _level(score: float) -> PropagationLevel:
    if score >= 0.90:
        return PropagationLevel.CRITICAL
    if score >= 0.65:
        return PropagationLevel.HIGH
    if score >= 0.35:
        return PropagationLevel.MEDIUM
    return PropagationLevel.LOW


def analyze_risk_propagation(
    records: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> RiskPropagationReport:
    normalized: list[dict[str, Any]] = []

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

        remaining = max(
            0.0,
            exposure - expected_recovery,
        )

        urgency = _ratio(
            record.get("urgency")
            or record.get("risk_urgency")
        )

        confidence = _ratio(
            record.get("confidence")
            or record.get("prediction_confidence")
        )

        evidence_quality = _ratio(
            record.get("evidence_quality")
            or record.get("evidence_score")
        )

        normalized.append({
            "entity_id": entity_id,
            "exposure": exposure,
            "remaining": remaining,
            "urgency": urgency,
            "confidence": confidence,
            "evidence_quality": evidence_quality,
        })

    total_exposure = sum(
        item["exposure"] for item in normalized
    )

    propagations: list[RiskPropagation] = []

    for item in normalized:
        entity_id = item["entity_id"]
        exposure = item["exposure"]
        remaining = item["remaining"]

        concentration = (
            exposure / total_exposure
            if total_exposure > 0
            else 0.0
        )

        # Propagation represents the portion of the remaining
        # revenue exposure that can materially influence the
        # broader revenue position.
        propagated_exposure = round(
            remaining * (1.0 + concentration),
            2,
        )

        propagation_score = round(
            min(
                1.0,
                (
                    0.40 * _ratio(concentration * 2.0)
                    + 0.30 * _ratio(
                        remaining / exposure
                        if exposure > 0
                        else 0
                    )
                    + 0.20 * item["urgency"]
                    + 0.10 * item["confidence"]
                ),
            ),
            4,
        )

        level = _level(propagation_score)

        dependency = RiskDependency(
            source_id=entity_id,
            target_id="revenue-system",
            relationship="REVENUE_EXPOSURE_TO_SYSTEM",
            propagated_exposure=propagated_exposure,
            evidence_ref=f"entity:{entity_id}",
        )

        risk_path = (
            entity_id,
            "REMAINING_EXPOSURE",
            "REVENUE_RISK",
            "SYSTEM_EXPOSURE",
        )

        explanation = (
            f"{entity_id} contributes "
            f"₹{exposure:,.2f} direct exposure and "
            f"₹{remaining:,.2f} remaining exposure. "
            f"Its concentration is {concentration:.2%}. "
            f"Potential propagated exposure is "
            f"₹{propagated_exposure:,.2f}. "
            f"Risk propagation score is "
            f"{propagation_score:.2f}. "
            f"This is an advisory risk relationship and "
            f"requires human review."
        )

        propagations.append(
            RiskPropagation(
                entity_id=entity_id,
                direct_exposure=exposure,
                remaining_exposure=remaining,
                concentration_ratio=round(concentration, 4),
                propagated_exposure=propagated_exposure,
                propagation_score=propagation_score,
                propagation_level=level,
                dependencies=(dependency,),
                risk_path=risk_path,
                explanation=explanation,
            )
        )

    propagations.sort(
        key=lambda item: (
            -item.propagation_score,
            -item.propagated_exposure,
            item.entity_id,
        )
    )

    return RiskPropagationReport(
        propagations=tuple(propagations),
        total_direct_exposure=round(
            sum(item.direct_exposure for item in propagations),
            2,
        ),
        total_remaining_exposure=round(
            sum(item.remaining_exposure for item in propagations),
            2,
        ),
        total_propagated_exposure=round(
            sum(item.propagated_exposure for item in propagations),
            2,
        ),
        highest_concentration=round(
            max(
                (item.concentration_ratio for item in propagations),
                default=0.0,
            ),
            4,
        ),
        critical_count=sum(
            item.propagation_level == PropagationLevel.CRITICAL
            for item in propagations
        ),
        high_count=sum(
            item.propagation_level == PropagationLevel.HIGH
            for item in propagations
        ),
    )
