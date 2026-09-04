from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _number(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class RevenueHealth:
    score: float
    status: str
    outstanding_revenue: float
    revenue_at_risk: float
    expected_collection: float
    remaining_exposure: float
    risk_ratio: float
    collection_ratio: float
    human_review_required: bool
    execution_allowed: bool
    financial_mutation: bool
    provider_mutation: bool
    read_only: bool


def calculate_revenue_health(
    *,
    outstanding_revenue: Any = 0,
    revenue_at_risk: Any = 0,
    expected_collection: Any = 0,
) -> RevenueHealth:

    outstanding = _number(outstanding_revenue)
    risk = min(_number(revenue_at_risk), outstanding)
    expected = min(_number(expected_collection), outstanding)

    if outstanding > 0:
        risk_ratio = risk / outstanding
        collection_ratio = expected / outstanding
    else:
        risk_ratio = 0.0
        collection_ratio = 0.0

    score = (
        100.0
        * (
            (1.0 - risk_ratio) * 0.60
            + collection_ratio * 0.40
        )
    )

    score = round(max(0.0, min(100.0, score)), 2)

    if score >= 80:
        status = "HEALTHY"
    elif score >= 60:
        status = "WATCH"
    elif score >= 40:
        status = "AT_RISK"
    else:
        status = "CRITICAL"

    return RevenueHealth(
        score=score,
        status=status,
        outstanding_revenue=round(outstanding, 2),
        revenue_at_risk=round(risk, 2),
        expected_collection=round(expected, 2),
        remaining_exposure=round(
            max(0.0, outstanding - expected),
            2,
        ),
        risk_ratio=round(risk_ratio, 4),
        collection_ratio=round(collection_ratio, 4),
        human_review_required=True,
        execution_allowed=False,
        financial_mutation=False,
        provider_mutation=False,
        read_only=True,
    )
