from revenex.phase9 import run_learning_loop


def test_missing_outcome_waits_safely():
    result = run_learning_loop(
        {
            "expected_collection": 483120,
        }
    )

    assert result.evaluation.status == "INSUFFICIENT_DATA"
    assert result.evaluation.actual_value is None
    assert result.evaluation.learning_signal == "WAIT_FOR_OUTCOME"
    assert result.learning_ready is False
    assert result.loop_state == "WAITING_FOR_OUTCOME"
    assert result.next_recommendation == "WAIT_FOR_REAL_WORLD_OUTCOME"


def test_accurate_prediction_generates_learning_signal():
    result = run_learning_loop(
        {
            "expected_collection": 100000,
            "actual_collection": 95000,
        }
    )

    assert result.evaluation.status == "EVALUATED"
    assert result.evaluation.variance == -5000
    assert result.evaluation.accuracy == 0.95
    assert result.evaluation.learning_signal == "PREDICTION_ACCURATE"
    assert result.learning_ready is True
    assert result.loop_state == "LEARNING_SIGNAL_READY"


def test_large_variance_requires_review():
    result = run_learning_loop(
        {
            "expected_collection": 100000,
            "actual_collection": 50000,
        }
    )

    assert result.evaluation.status == "EVALUATED"
    assert result.evaluation.accuracy == 0.5
    assert (
        result.evaluation.learning_signal
        == "PREDICTION_REVIEW_REQUIRED"
    )
    assert result.learning_ready is True
    assert result.loop_state == "LEARNING_REVIEW_REQUIRED"
    assert (
        result.next_recommendation
        == "REVIEW_PREDICTION_ASSUMPTIONS"
    )


def test_learning_never_mutates_model_or_finances():
    result = run_learning_loop(
        {
            "expected_collection": 100000,
            "actual_collection": 95000,
        }
    )

    assert result.human_review_required is True
    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.automatic_action is False
    assert result.model_mutation is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False

    assert result.evaluation.model_mutation is False
    assert result.evaluation.financial_mutation is False
    assert result.evaluation.provider_mutation is False


def test_zero_expected_value_is_safe():
    result = run_learning_loop(
        {
            "expected_collection": 0,
            "actual_collection": 0,
        }
    )

    assert result.evaluation.status == "EVALUATED"
    assert result.evaluation.accuracy == 1.0
    assert (
        result.evaluation.learning_signal
        == "PREDICTION_ACCURATE"
    )
