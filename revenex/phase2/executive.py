from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _money(value: Any) -> float:
    try:
        return round(max(0.0, float(value or 0)), 2)
    except (TypeError, ValueError):
        return 0.0


def _confidence(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value or 0))), 4)
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class ExecutiveDashboard:
    outstanding_revenue: float
    revenue_at_risk: float
    expected_collection: float
    remaining_exposure: float
    recovery_opportunity: float
    confidence: float
    risk_level: str
    recommended_action: str
    decision_status: str
    human_approval_required: bool
    execution_allowed: bool
    automatic_action: bool
    financial_mutation: bool
    provider_mutation: bool
    read_only: bool


def build_executive_dashboard(
    *,
    outstanding_revenue: Any = 0,
    revenue_at_risk: Any = 0,
    expected_collection: Any = 0,
    confidence: Any = 0,
    risk_level: str = "REVIEW",
    recommended_action: str = "HUMAN_REVIEW",
) -> ExecutiveDashboard:

    outstanding = _money(outstanding_revenue)
    risk = _money(revenue_at_risk)
    expected = _money(expected_collection)

    remaining = round(
        max(0.0, outstanding - expected),
        2,
    )

    recovery = round(
        min(risk, expected),
        2,
    )

    if risk >= outstanding * 0.75 and outstanding > 0:
        normalized_risk = "CRITICAL"
    elif risk >= outstanding * 0.50 and outstanding > 0:
        normalized_risk = "HIGH"
    elif risk > 0:
        normalized_risk = "MEDIUM"
    else:
        normalized_risk = "LOW"

    return ExecutiveDashboard(
        outstanding_revenue=outstanding,
        revenue_at_risk=risk,
        expected_collection=expected,
        remaining_exposure=remaining,
        recovery_opportunity=recovery,
        confidence=_confidence(confidence),
        risk_level=str(risk_level or normalized_risk),
        recommended_action=str(
            recommended_action or "HUMAN_REVIEW"
        ),
        decision_status="ADVISORY",
        human_approval_required=True,
        execution_allowed=False,
        automatic_action=False,
        financial_mutation=False,
        provider_mutation=False,
        read_only=True,
    )
