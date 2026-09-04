from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionEvidence:
    decision: str
    scenario: str
    expected_collection: float
    remaining_exposure: float
    confidence: float
    evidence_count: int
    explainable: bool
    human_approval_required: bool
    execution_allowed: bool
    financial_mutation: bool
    provider_mutation: bool
    read_only: bool


def _money(value: Any) -> float:
    try:
        return round(max(0.0, float(value or 0)), 2)
    except (TypeError, ValueError):
        return 0.0


def build_decision_evidence(
    *,
    decision: str = "HUMAN_REVIEW",
    scenario: str = "REVIEW",
    expected_collection: Any = 0,
    remaining_exposure: Any = 0,
    confidence: Any = 0,
    evidence: list[Any] | None = None,
) -> DecisionEvidence:

    try:
        normalized_confidence = max(
            0.0,
            min(1.0, float(confidence or 0)),
        )
    except (TypeError, ValueError):
        normalized_confidence = 0.0

    evidence_count = len(evidence or [])

    return DecisionEvidence(
        decision=str(decision),
        scenario=str(scenario),
        expected_collection=_money(expected_collection),
        remaining_exposure=_money(remaining_exposure),
        confidence=round(normalized_confidence, 4),
        evidence_count=evidence_count,
        explainable=evidence_count > 0,
        human_approval_required=True,
        execution_allowed=False,
        financial_mutation=False,
        provider_mutation=False,
        read_only=True,
    )
