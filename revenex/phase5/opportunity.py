from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Opportunity:
    opportunity_id: str
    category: str
    exposure: float
    recoverable_value: float
    priority_score: float
    priority: str
    confidence: float
    evidence_quality: float
    rationale: str
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class OpportunityReport:
    opportunities: tuple[Opportunity, ...]
    total_opportunities: int
    total_exposure: float
    total_recoverable_value: float
    highest_priority: str
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _score(exposure: float, probability: float, urgency: float, confidence: float) -> float:
    raw = (
        min(exposure / 100000.0, 1.0) * 0.35
        + probability * 0.25
        + urgency * 0.20
        + confidence * 0.20
    )
    return round(min(max(raw, 0.0), 1.0), 4)


def analyze_opportunities(
    items: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> OpportunityReport:
    results: list[Opportunity] = []

    for index, item in enumerate(items):
        opportunity_id = str(
            item.get("opportunity_id")
            or item.get("id")
            or item.get("resource_id")
            or f"opportunity-{index + 1}"
        )

        exposure = _money(
            item.get("exposure")
            or item.get("revenue_at_risk")
            or item.get("outstanding")
        )

        recoverable_value = _money(
            item.get("recoverable_value")
            or item.get("expected_recovery")
            or item.get("expected_collection")
        )

        probability = min(max(float(item.get("probability", 0.0) or 0.0), 0.0), 1.0)
        urgency = min(max(float(item.get("urgency", 0.0) or 0.0), 0.0), 1.0)
        confidence = min(max(float(item.get("confidence", 0.0) or 0.0), 0.0), 1.0)
        evidence_quality = min(
            max(float(item.get("evidence_quality", 0.0) or 0.0), 0.0),
            1.0,
        )

        score = _score(
            exposure,
            probability,
            urgency,
            confidence,
        )

        if score >= 0.80:
            priority = "CRITICAL"
        elif score >= 0.60:
            priority = "HIGH"
        elif score >= 0.40:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        category = str(
            item.get("category")
            or item.get("type")
            or "REVENUE_RECOVERY"
        )

        rationale = (
            f"{priority} opportunity based on "
            f"₹{exposure:,.2f} exposure, "
            f"{confidence:.0%} confidence, and "
            f"{evidence_quality:.0%} evidence quality."
        )

        results.append(
            Opportunity(
                opportunity_id=opportunity_id,
                category=category,
                exposure=round(exposure, 2),
                recoverable_value=round(recoverable_value, 2),
                priority_score=score,
                priority=priority,
                confidence=round(confidence, 4),
                evidence_quality=round(evidence_quality, 4),
                rationale=rationale,
            )
        )

    results.sort(
        key=lambda x: (x.priority_score, x.recoverable_value),
        reverse=True,
    )

    highest_priority = (
        results[0].priority
        if results
        else "NONE"
    )

    return OpportunityReport(
        opportunities=tuple(results),
        total_opportunities=len(results),
        total_exposure=round(sum(x.exposure for x in results), 2),
        total_recoverable_value=round(
            sum(x.recoverable_value for x in results),
            2,
        ),
        highest_priority=highest_priority,
    )
