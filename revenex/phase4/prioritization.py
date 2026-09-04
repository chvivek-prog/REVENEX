from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _number(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class Opportunity:
    resource_id: str
    exposure: float
    probability: float
    expected_value: float
    urgency: float
    priority_score: float
    priority: str
    recommended_action: str
    human_review_required: bool
    execution_allowed: bool
    financial_mutation: bool
    provider_mutation: bool


def prioritize_opportunities(
    records: list[dict[str, Any]],
) -> list[Opportunity]:

    results: list[Opportunity] = []

    for index, record in enumerate(records):
        resource_id = str(
            record.get("resource_id")
            or record.get("customer_id")
            or f"resource-{index + 1}"
        )

        exposure = _number(
            record.get("exposure")
            or record.get("outstanding")
            or record.get("amount")
        )

        probability = min(
            1.0,
            _number(
                record.get("probability")
                or record.get("recovery_probability")
            ),
        )

        urgency = min(
            1.0,
            _number(record.get("urgency")),
        )

        expected_value = round(
            exposure * probability,
            2,
        )

        priority_score = round(
            (
                probability * 0.40
                + urgency * 0.25
                + min(
                    expected_value / max(exposure, 1.0),
                    1.0,
                ) * 0.35
            ),
            4,
        )

        if priority_score >= 0.80:
            priority = "CRITICAL"
            action = "URGENT_REVIEW"
        elif priority_score >= 0.60:
            priority = "HIGH"
            action = "RECOVERY_REVIEW"
        elif priority_score >= 0.35:
            priority = "MEDIUM"
            action = "MONITOR"
        else:
            priority = "LOW"
            action = "MONITOR"

        results.append(
            Opportunity(
                resource_id=resource_id,
                exposure=round(exposure, 2),
                probability=round(probability, 4),
                expected_value=expected_value,
                urgency=round(urgency, 4),
                priority_score=priority_score,
                priority=priority,
                recommended_action=action,
                human_review_required=True,
                execution_allowed=False,
                financial_mutation=False,
                provider_mutation=False,
            )
        )

    return sorted(
        results,
        key=lambda item: (
            -item.priority_score,
            -item.expected_value,
            item.resource_id,
        ),
    )
