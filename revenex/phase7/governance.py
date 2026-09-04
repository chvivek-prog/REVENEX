from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionTrace:
    trace_id: str
    decision: str
    scenario: str
    confidence: float
    expected_value: float
    remaining_exposure: float
    evidence: tuple[str, ...]
    risks: tuple[str, ...]
    alternatives: tuple[str, ...]
    rationale: str
    governance_state: str
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class GovernanceReport:
    traces: tuple[DecisionTrace, ...]
    total_decisions: int
    decisions_requiring_review: int
    high_risk_decisions: int
    audit_complete: bool
    governance_state: str
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _confidence(value: Any) -> float:
    try:
        return min(max(float(value or 0), 0.0), 1.0)
    except (TypeError, ValueError):
        return 0.0


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        return (value,)

    try:
        return tuple(str(item) for item in value)
    except TypeError:
        return (str(value),)


def _risk_level(
    confidence: float,
    remaining_exposure: float,
    evidence: tuple[str, ...],
) -> str:
    if not evidence or confidence < 0.40:
        return "HIGH"

    if remaining_exposure > 0 and confidence < 0.70:
        return "MEDIUM"

    return "LOW"


def build_decision_trace(
    decisions: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> GovernanceReport:
    traces: list[DecisionTrace] = []

    for index, item in enumerate(decisions):
        trace_id = str(
            item.get("trace_id")
            or item.get("decision_id")
            or f"trace-{index + 1}"
        )

        decision = str(
            item.get("decision")
            or item.get("recommended_action")
            or "REVIEW"
        )

        scenario = str(
            item.get("scenario")
            or "UNKNOWN"
        )

        confidence = _confidence(
            item.get("confidence")
        )

        expected_value = _money(
            item.get("expected_value")
            or item.get("expected_collection")
        )

        remaining_exposure = _money(
            item.get("remaining_exposure")
            or item.get("remaining_exposure_value")
        )

        evidence = _tuple(
            item.get("evidence")
            or item.get("evidence_items")
        )

        risks = _tuple(
            item.get("risks")
            or item.get("risk_factors")
        )

        alternatives = _tuple(
            item.get("alternatives")
            or item.get("alternative_actions")
        )

        risk_level = _risk_level(
            confidence,
            remaining_exposure,
            evidence,
        )

        if risk_level == "HIGH":
            governance_state = "HUMAN_REVIEW_REQUIRED"
        elif risk_level == "MEDIUM":
            governance_state = "REVIEW_RECOMMENDED"
        else:
            governance_state = "ADVISORY"

        if not risks:
            risks = (
                f"Remaining exposure: ₹{remaining_exposure:,.2f}",
            )

        rationale = (
            f"Decision={decision}; "
            f"scenario={scenario}; "
            f"confidence={confidence:.0%}; "
            f"expected value=₹{expected_value:,.2f}; "
            f"risk={risk_level}. "
            f"Recommendation remains advisory and requires human control."
        )

        traces.append(
            DecisionTrace(
                trace_id=trace_id,
                decision=decision,
                scenario=scenario,
                confidence=round(confidence, 4),
                expected_value=round(expected_value, 2),
                remaining_exposure=round(remaining_exposure, 2),
                evidence=evidence,
                risks=risks,
                alternatives=alternatives,
                rationale=rationale,
                governance_state=governance_state,
            )
        )

    high_risk = sum(
        1
        for trace in traces
        if trace.governance_state == "HUMAN_REVIEW_REQUIRED"
    )

    review_required = sum(
        1
        for trace in traces
        if trace.human_review_required
    )

    return GovernanceReport(
        traces=tuple(traces),
        total_decisions=len(traces),
        decisions_requiring_review=review_required,
        high_risk_decisions=high_risk,
        audit_complete=True,
        governance_state=(
            "HUMAN_REVIEW_REQUIRED"
            if high_risk
            else "ADVISORY"
        ),
    )
