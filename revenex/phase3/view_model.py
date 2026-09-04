from __future__ import annotations

from dataclasses import asdict, dataclass
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
class DashboardViewModel:
    title: str

    outstanding_revenue: float
    revenue_at_risk: float
    expected_collection: float
    remaining_exposure: float
    confidence: float

    risk_level: str
    scenario: str
    recommended_action: str
    decision_status: str

    human_approval_required: bool
    execution_allowed: bool
    automatic_action: bool
    financial_mutation: bool
    provider_mutation: bool
    read_only: bool

    pipeline: tuple[str, ...]
    safety_message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_dashboard_view_model(
    *,
    outstanding_revenue: Any = 0,
    revenue_at_risk: Any = 0,
    expected_collection: Any = 0,
    confidence: Any = 0,
    risk_level: str = "REVIEW",
    scenario: str = "REVIEW",
    recommended_action: str = "HUMAN_REVIEW",
) -> DashboardViewModel:

    outstanding = _money(outstanding_revenue)
    risk = _money(revenue_at_risk)
    expected = _money(expected_collection)

    return DashboardViewModel(
        title="REVENEX Revenue Command Center",
        outstanding_revenue=outstanding,
        revenue_at_risk=risk,
        expected_collection=expected,
        remaining_exposure=round(
            max(0.0, outstanding - expected),
            2,
        ),
        confidence=_confidence(confidence),
        risk_level=str(risk_level or "REVIEW"),
        scenario=str(scenario or "REVIEW"),
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
        pipeline=(
            "OBSERVE",
            "INVESTIGATE",
            "PREDICT",
            "SIMULATE",
            "DECIDE",
            "EXPLAIN",
            "AUDIT",
            "OUTCOME",
            "LEARN",
        ),
        safety_message=(
            "REVENEX is advisory-only. "
            "Human approval is required before any action."
        ),
    )
