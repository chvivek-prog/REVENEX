from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _money(value: Any) -> float:
    try:
        return round(max(0.0, float(value or 0)), 2)
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class ExecutiveRevenueState:
    outstanding_revenue: float
    revenue_at_risk: float
    expected_collection: float
    expected_remaining_exposure: float
    recovery_opportunity: float
    confidence: float
    priority: str
    recommended_action: str
    human_approval_required: bool
    execution_allowed: bool
    automatic_action: bool
    financial_mutation: bool
    provider_mutation: bool
    read_only: bool


def build_executive_revenue_state(
    *,
    outstanding_revenue: Any = 0,
    revenue_at_risk: Any = 0,
    expected_collection: Any = 0,
    confidence: Any = 0,
    priority: str = "REVIEW",
    recommended_action: str = "HUMAN_REVIEW",
) -> ExecutiveRevenueState:
    outstanding = _money(outstanding_revenue)
    risk = _money(revenue_at_risk)
    expected = _money(expected_collection)

    remaining = round(
        max(0.0, outstanding - expected),
        2,
    )

    recovery_opportunity = round(
        max(0.0, min(risk, expected)),
        2,
    )

    try:
        normalized_confidence = max(
            0.0,
            min(1.0, float(confidence)),
        )
    except (TypeError, ValueError):
        normalized_confidence = 0.0

    return ExecutiveRevenueState(
        outstanding_revenue=outstanding,
        revenue_at_risk=risk,
        expected_collection=expected,
        expected_remaining_exposure=remaining,
        recovery_opportunity=recovery_opportunity,
        confidence=round(normalized_confidence, 4),
        priority=str(priority or "REVIEW"),
        recommended_action=str(
            recommended_action or "HUMAN_REVIEW"
        ),
        human_approval_required=True,
        execution_allowed=False,
        automatic_action=False,
        financial_mutation=False,
        provider_mutation=False,
        read_only=True,
    )
