"""
REVENEX Stage 38 — Decision Explainability & Audit Trace.

Creates a deterministic, immutable explanation of a revenue
intelligence decision.

This layer records what REVENEX decided and why.
It does not execute the decision.
"""

from dataclasses import dataclass

from revenex.decision.engine import DecisionRecommendation


@dataclass(frozen=True)
class DecisionAuditTrace:
    decision: str
    scenario: str | None
    expected_collection: float
    remaining_exposure: float
    confidence: float

    rationale: tuple[str, ...]
    evidence: tuple[str, ...]

    requires_approval: bool
    execution_allowed: bool

    automatic_action: bool
    financial_mutation: bool
    provider_mutation: bool

    stages: tuple[str, ...]


def build_decision_audit_trace(
    decision: DecisionRecommendation,
) -> DecisionAuditTrace:
    """
    Convert a decision recommendation into an immutable audit trace.
    """

    scenario = (
        decision.scenario.value
        if decision.scenario is not None
        else None
    )

    decision_name = (
        decision.recommended_action
    )

    evidence = (
        f"expected_collection={decision.expected_collection:.2f}",
        f"remaining_exposure={decision.remaining_exposure:.2f}",
        f"confidence={decision.confidence:.4f}",
        f"scenario={scenario or 'NONE'}",
    )

    return DecisionAuditTrace(
        decision=decision_name,
        scenario=scenario,
        expected_collection=decision.expected_collection,
        remaining_exposure=decision.remaining_exposure,
        confidence=decision.confidence,
        rationale=decision.rationale,
        evidence=evidence,
        requires_approval=True,
        execution_allowed=False,
        automatic_action=False,
        financial_mutation=False,
        provider_mutation=False,
        stages=(
            "OBSERVE",
            "INVESTIGATE",
            "PREDICT",
            "SIMULATE",
            "DECIDE",
            "EXPLAIN",
            "AUDIT",
        ),
    )


def explain_decision(
    decision: DecisionRecommendation,
) -> DecisionAuditTrace:
    """
    Canonical Stage 38 explanation boundary.
    """

    return build_decision_audit_trace(decision)
