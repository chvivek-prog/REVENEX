
from revenex.outcome.intelligence import (
    OutcomeIntelligenceStatus,
    OutcomeRecord,
    PredictionBias,
    aggregate_outcomes,
    evaluate_outcome_intelligence,
)


def observed(
    decision_id="d1",
    expected=483120,
    actual=470000,
    expected_exposure=66880,
    actual_exposure=80000,
):
    return OutcomeRecord(
        decision_id=decision_id,
        expected_collection=expected,
        actual_collection=actual,
        expected_remaining_exposure=expected_exposure,
        actual_remaining_exposure=actual_exposure,
    )


def test_real_outcome_is_evaluated():

    result = evaluate_outcome_intelligence(
        observed()
    )

    assert (
        result.status
        == OutcomeIntelligenceStatus.EVALUATED
    )

    assert result.collection_variance == -13120
    assert (
        round(
            result.collection_accuracy,
            4,
        )
        == 0.9728
    )

    assert (
        result.prediction_bias
        == PredictionBias.ALIGNED
    )

    assert (
        result.learning_signal
        == "PREDICTION_ALIGNED"
    )


def test_underprediction_is_detected():

    result = evaluate_outcome_intelligence(
        observed(
            expected=100000,
            actual=120000,
        )
    )

    assert (
        result.prediction_bias
        == PredictionBias.UNDERPREDICTING
    )

    assert (
        result.learning_signal
        == "UNDERPREDICTED_COLLECTION"
    )


def test_overprediction_is_detected():

    result = evaluate_outcome_intelligence(
        observed(
            expected=100000,
            actual=70000,
        )
    )

    assert (
        result.prediction_bias
        == PredictionBias.OVERPREDICTING
    )

    assert (
        result.learning_signal
        == "OVERPREDICTED_COLLECTION"
    )


def test_missing_outcome_is_not_invented():

    result = evaluate_outcome_intelligence(
        OutcomeRecord(
            decision_id="pending",
            expected_collection=483120,
            actual_collection=None,
            expected_remaining_exposure=66880,
            actual_remaining_exposure=None,
        )
    )

    assert (
        result.status
        == OutcomeIntelligenceStatus.INSUFFICIENT_DATA
    )

    assert result.actual_collection is None
    assert result.collection_accuracy is None
    assert (
        result.prediction_bias
        == PredictionBias.INSUFFICIENT_DATA
    )

    assert (
        result.learning_signal
        == "WAIT_FOR_OUTCOME"
    )


def test_aggregate_detects_bias():

    evaluations = [
        evaluate_outcome_intelligence(
            observed(
                decision_id="1",
                expected=100000,
                actual=120000,
            )
        ),
        evaluate_outcome_intelligence(
            observed(
                decision_id="2",
                expected=100000,
                actual=115000,
            )
        ),
        evaluate_outcome_intelligence(
            observed(
                decision_id="3",
                expected=100000,
                actual=90000,
            )
        ),
    ]

    report = aggregate_outcomes(
        evaluations
    )

    assert report.evaluated_count == 3
    assert report.underpredicting_count == 2
    assert report.overpredicting_count == 1

    assert (
        report.model_bias
        == PredictionBias.UNDERPREDICTING
    )

    assert report.learning_confidence > 0


def test_empty_history_requires_more_outcomes():

    report = aggregate_outcomes([])

    assert report.evaluated_count == 0
    assert (
        report.model_bias
        == PredictionBias.INSUFFICIENT_DATA
    )

    assert report.learning_confidence == 0.0


def test_learning_never_mutates_model():

    result = evaluate_outcome_intelligence(
        observed()
    )

    assert (
        result.automatic_model_mutation
        is False
    )

    assert (
        result.financial_mutation
        is False
    )

    assert (
        result.provider_mutation
        is False
    )

    assert (
        result.human_review_required
        is True
    )
