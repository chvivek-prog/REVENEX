from revenex.loop.closed_loop import (
    evaluate_closed_loop_outcome,
    run_closed_loop,
)
from revenex.outcome.tracking import OutcomeStatus


def test_closed_loop_connects_risk_decision_audit_outcome_learning():
    result = run_closed_loop(
        [
            {
                "customer_id": "customer-1",
                "amount": 200000,
                "outstanding_amount": 150000,
                "days_overdue": 90,
            }
        ],
        [],
        decision_id="decision-41",
    )

    assert result.risk_report.total_outstanding == 150000
    assert result.decision is not None
    assert result.audit_trace is not None
    assert result.outcome is not None
    assert result.outcome_evaluation is not None
    assert result.learning_report is not None
    assert result.learning_action == "WAIT_FOR_MORE_OUTCOMES"


def test_closed_loop_starts_without_an_assumed_outcome():
    result = run_closed_loop(
        [],
        [],
        decision_id="decision-empty",
    )

    assert result.outcome is not None
    assert (
        result.outcome.status
        == OutcomeStatus.PENDING
    )

    assert (
        result.outcome_evaluation.status
        == OutcomeStatus.INSUFFICIENT_DATA
    )


def test_closed_loop_can_consume_observed_outcome():
    result = run_closed_loop(
        [
            {
                "customer_id": "customer-1",
                "amount": 100000,
                "outstanding_amount": 80000,
                "days_overdue": 60,
            }
        ],
        [],
        decision_id="decision-observed",
    )

    updated = evaluate_closed_loop_outcome(
        result,
        actual_collection=50000,
        actual_remaining_exposure=30000,
    )

    assert (
        updated.outcome.actual_collection
        == 50000
    )

    assert (
        updated.outcome_evaluation.status
        in {
            OutcomeStatus.SUCCESS,
            OutcomeStatus.PARTIAL,
        }
    )

    assert (
        updated.learning_report.evaluated_count
        == 1
    )


def test_closed_loop_is_approval_gated():
    result = run_closed_loop(
        [
            {
                "customer_id": "customer-1",
                "amount": 500000,
                "outstanding_amount": 400000,
                "days_overdue": 120,
            }
        ],
        [],
    )

    assert result.execution_allowed is False
    assert result.automatic_action is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False


def test_observed_outcome_does_not_mutate_original_result():
    result = run_closed_loop(
        [
            {
                "customer_id": "customer-1",
                "amount": 100000,
                "outstanding_amount": 60000,
                "days_overdue": 60,
            }
        ],
        [],
    )

    updated = evaluate_closed_loop_outcome(
        result,
        actual_collection=40000,
        actual_remaining_exposure=20000,
    )

    assert result.outcome.actual_collection is None
    assert updated.outcome.actual_collection == 40000
