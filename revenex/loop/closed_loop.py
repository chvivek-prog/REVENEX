"""
REVENEX Stage 41 — Closed-Loop Intelligence.

Connects prediction, simulation, decision, audit, outcome evaluation,
and learning into one deterministic intelligence loop.

This coordinator is advisory-only. It never executes financial,
provider, payment, refund, or recovery mutations.
"""

from dataclasses import dataclass
from typing import Any

from revenex.audit.decision_trace import (
    DecisionAuditTrace,
    explain_decision,
)
from revenex.decision.engine import (
    DecisionRecommendation,
    decide_recovery,
)
from revenex.learning.engine import (
    LearningReport,
    build_learning_report,
    recommend_learning_action,
)
from revenex.outcome.tracking import (
    OutcomeEvaluation,
    OutcomeEvent,
    evaluate_outcome,
    record_observed_outcome,
)
from revenex.risk.revenue_risk import (
    RevenueRiskReport,
    build_revenue_risk_report,
)


@dataclass(frozen=True)
class ClosedLoopResult:
    risk_report: RevenueRiskReport
    decision: DecisionRecommendation
    audit_trace: DecisionAuditTrace

    outcome: OutcomeEvent | None
    outcome_evaluation: OutcomeEvaluation | None

    learning_report: LearningReport
    learning_action: str

    execution_allowed: bool
    automatic_action: bool
    financial_mutation: bool
    provider_mutation: bool


def run_closed_loop(
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    decision_id: str = "decision-1",
) -> ClosedLoopResult:
    """
    Run the advisory intelligence loop.

    No actual outcome is assumed. The outcome remains pending until
    an observed result is explicitly supplied.
    """

    risk_report = build_revenue_risk_report(
        invoices,
        payments,
    )

    decision = decide_recovery(
        risk_report.total_outstanding,
        max(
            (
                risk.late_payment_risk
                for risk in risk_report.customer_risks
            ),
            default=0.0,
        ),
    )

    audit_trace = explain_decision(
        decision
    )

    outcome = OutcomeEvent(
        decision_id=str(decision_id),
        customer_id="portfolio",
        expected_collection=decision.expected_collection,
        actual_collection=None,
        expected_remaining_exposure=decision.remaining_exposure,
        actual_remaining_exposure=None,
        status="PENDING",
        evidence=(
            "Awaiting observed outcome.",
        ),
    )

    outcome_evaluation = evaluate_outcome(
        outcome
    )

    learning_report = build_learning_report(
        (outcome_evaluation,)
    )

    learning_action = recommend_learning_action(
        learning_report
    )

    return ClosedLoopResult(
        risk_report=risk_report,
        decision=decision,
        audit_trace=audit_trace,
        outcome=outcome,
        outcome_evaluation=outcome_evaluation,
        learning_report=learning_report,
        learning_action=learning_action,
        execution_allowed=False,
        automatic_action=False,
        financial_mutation=False,
        provider_mutation=False,
    )


def evaluate_closed_loop_outcome(
    result: ClosedLoopResult,
    actual_collection: float,
    actual_remaining_exposure: float,
) -> ClosedLoopResult:
    """
    Feed an observed outcome back into the learning loop.

    Returns a new immutable result; the original result is unchanged.
    """

    if result.outcome is None:
        raise ValueError(
            "Closed-loop result has no outcome to evaluate."
        )

    observed = record_observed_outcome(
        result.outcome,
        actual_collection=actual_collection,
        actual_remaining_exposure=actual_remaining_exposure,
    )

    evaluation = evaluate_outcome(
        observed
    )

    learning_report = build_learning_report(
        (evaluation,)
    )

    learning_action = recommend_learning_action(
        learning_report
    )

    return ClosedLoopResult(
        risk_report=result.risk_report,
        decision=result.decision,
        audit_trace=result.audit_trace,
        outcome=observed,
        outcome_evaluation=evaluation,
        learning_report=learning_report,
        learning_action=learning_action,
        execution_allowed=False,
        automatic_action=False,
        financial_mutation=False,
        provider_mutation=False,
    )
