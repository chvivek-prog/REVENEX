from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _money(value: Any) -> float:
    try:
        return round(max(0.0, float(value or 0)), 2)
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class RiskItem:
    resource_id: str
    exposure: float
    risk_score: float
    priority: str
    recommended_action: str
    human_review_required: bool
    execution_allowed: bool
    financial_mutation: bool
    provider_mutation: bool


def build_risk_priorities(
    records: list[dict[str, Any]],
) -> list[RiskItem]:

    results: list[RiskItem] = []

    for index, record in enumerate(records):
        resource_id = str(
            record.get("resource_id")
            or record.get("customer_id")
            or f"resource-{index + 1}"
        )

        exposure = _money(
            record.get("exposure")
            or record.get("outstanding")
            or record.get("amount")
        )

        try:
            risk_score = max(
                0.0,
                min(
                    1.0,
                    float(record.get("risk_score") or 0),
                ),
            )
        except (TypeError, ValueError):
            risk_score = 0.0

        if risk_score >= 0.80:
            priority = "CRITICAL"
            action = "URGENT_REVIEW"
        elif risk_score >= 0.60:
            priority = "HIGH"
            action = "RECOVERY_REVIEW"
        elif risk_score >= 0.30:
            priority = "MEDIUM"
            action = "MONITOR"
        else:
            priority = "LOW"
            action = "MONITOR"

        results.append(
            RiskItem(
                resource_id=resource_id,
                exposure=exposure,
                risk_score=round(risk_score, 4),
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
            -item.risk_score,
            -item.exposure,
            item.resource_id,
        ),
    )
