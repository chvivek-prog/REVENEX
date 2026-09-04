from revenex.outcome.tracking import (
    OutcomeStatus,
    create_outcome_event,
    evaluate_outcome,
    record_observed_outcome,
)


def test_new_outcome_is_pending():
    outcome = create_outcome_event(
        "decision-1",
        "customer-1",
        60000,
        40000,
    )

    assert outcome.status == OutcomeStatus.PENDING
    assert outcome.actual_collection is None
    assert outcome.actual_remaining_exposure is None


def test_missing_actual_data_is_insufficient():
    outcome = create_outcome_event(
        "decision-1",
        "customer-1",
        60000,
        40000,
    )

    evaluation = evaluate_outcome(outcome)

    assert evaluation.status == OutcomeStatus.INSUFFICIENT_DATA
    assert evaluation.learning_signal == "WAIT_FOR_OUTCOME"


def test_successful_outcome_is_detected():
    pending = create_outcome_event(
        "decision-1",
        "customer-1",
        60000,
        40000,
    )

    observed = record_observed_outcome(
        pending,
        actual_collection=58000,
        actual_remaining_exposure=42000,
    )

    evaluation = evaluate_outcome(observed)

    assert evaluation.status == OutcomeStatus.SUCCESS
    assert evaluation.collection_variance == -2000
    assert evaluation.collection_accuracy is not None
    assert evaluation.collection_accuracy > 0.90
    assert evaluation.learning_signal == "PREDICTION_ALIGNED"


def test_underprediction_creates_learning_signal():
    pending = create_outcome_event(
        "decision-2",
        "customer-2",
        50000,
        50000,
    )

    observed = record_observed_outcome(
        pending,
        actual_collection=80000,
        actual_remaining_exposure=20000,
    )

    evaluation = evaluate_outcome(observed)

    assert evaluation.learning_signal == "UNDERPREDICTED_COLLECTION"
    assert evaluation.collection_variance == 30000


def test_overprediction_creates_learning_signal():
    pending = create_outcome_event(
        "decision-3",
        "customer-3",
        80000,
        20000,
    )

    observed = record_observed_outcome(
        pending,
        actual_collection=30000,
        actual_remaining_exposure=70000,
    )

    evaluation = evaluate_outcome(observed)

    assert evaluation.learning_signal == "OVERPREDICTED_COLLECTION"
    assert evaluation.collection_variance == -50000


def test_outcome_tracking_is_immutable():
    pending = create_outcome_event(
        "decision-4",
        "customer-4",
        100000,
        50000,
    )

    observed = record_observed_outcome(
        pending,
        actual_collection=70000,
        actual_remaining_exposure=80000,
    )

    assert pending.actual_collection is None
    assert observed.actual_collection == 70000
    assert pending.actual_remaining_exposure is None
