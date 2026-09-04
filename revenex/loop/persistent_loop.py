"""
REVENEX Stage 43 — Persistent Closed-Loop Intelligence.

Connects the Stage 41 closed-loop coordinator with the Stage 42
durable outcome/learning store.

Advisory-only:
    execution_allowed = False
    automatic_action = False
    financial_mutation = False
    provider_mutation = False
"""

from dataclasses import dataclass
from typing import Any

from revenex.audit.decision_trace import explain_decision
from revenex.learning.engine import (
    build_learning_report,
    build_learning_signal,
    recommend_learning_action,
)
from revenex.outcome.tracking import evaluate_outcome
from revenex.persistence.outcome_store import (
    OutcomeStore,
    StoredOutcome,
)
from revenex.risk.revenue_risk import build_revenue_risk_report
from revenex.decision.engine import decide_recovery


@dataclass(frozen=True)
class PersistentLoopResult:
    decision_id: str
    customer_id: str

    decision: Any
    audit_trace: Any
    stored_outcome: StoredOutcome

    learning_action: str

    execution_allowed: bool
    automatic_action: bool
    financial_mutation: bool
    provider_mutation: bool


def start_persistent_loop(
    store: OutcomeStore,
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    decision_id: str,
    customer_id: str = "portfolio",
) -> PersistentLoopResult:
    """
    Run intelligence and persist its pending outcome.
    """

    risk_report = build_revenue_risk_report(
        invoices,
        payments,
    )

    risk_score = max(
        (
            risk.late_payment_risk
            for risk in risk_report.customer_risks
        ),
        default=0.0,
    )

    decision = decide_recovery(
        risk_report.total_outstanding,
        risk_score,
    )

    audit_trace = explain_decision(
        decision
    )

    stored_outcome = store.create_outcome(
        decision_id=decision_id,
        customer_id=customer_id,
        expected_collection=decision.expected_collection,
        expected_remaining_exposure=decision.remaining_exposure,
    )

    return PersistentLoopResult(
        decision_id=decision_id,
        customer_id=customer_id,
        decision=decision,
        audit_trace=audit_trace,
        stored_outcome=stored_outcome,
        learning_action="WAIT_FOR_OUTCOME",
        execution_allowed=False,
        automatic_action=False,
        financial_mutation=False,
        provider_mutation=False,
    )


def record_persistent_outcome(
    store: OutcomeStore,
    result: PersistentLoopResult,
    actual_collection: float,
    actual_remaining_exposure: float,
) -> PersistentLoopResult:
    """
    Persist an observed outcome, evaluate it, persist its learning
    signal, and return the updated immutable loop result.
    """

    stored = store.record_outcome(
        decision_id=result.decision_id,
        actual_collection=actual_collection,
        actual_remaining_exposure=actual_remaining_exposure,
    )

    outcome = result.stored_outcome

    from revenex.outcome.tracking import OutcomeEvent

    event = OutcomeEvent(
        decision_id=stored.decision_id,
        customer_id=stored.customer_id,
        expected_collection=stored.expected_collection,
        actual_collection=stored.actual_collection,
        expected_remaining_exposure=(
            stored.expected_remaining_exposure
        ),
        actual_remaining_exposure=(
            stored.actual_remaining_exposure
        ),
        status=stored.status,
        evidence=(
            "Persisted observed outcome loaded for evaluation.",
        ),
    )

    evaluation = evaluate_outcome(
        event
    )

    signal = build_learning_signal(
        evaluation
    )

    store.record_evaluation(
        decision_id=result.decision_id,
        status=evaluation.status.value,
        collection_variance=evaluation.collection_variance,
        collection_accuracy=evaluation.collection_accuracy,
        exposure_variance=evaluation.exposure_variance,
        learning_signal=evaluation.learning_signal,
    )

    store.record_learning_signal(
        decision_id=result.decision_id,
        signal=signal.signal,
        strength=signal.strength,
        evidence="; ".join(signal.evidence),
    )

    report = build_learning_report(
        (evaluation,)
    )

    return PersistentLoopResult(
        decision_id=result.decision_id,
        customer_id=result.customer_id,
        decision=result.decision,
        audit_trace=result.audit_trace,
        stored_outcome=stored,
        learning_action=recommend_learning_action(
            report
        ),
        execution_allowed=False,
        automatic_action=False,
        financial_mutation=False,
        provider_mutation=False,
    )
