from revenex.learning.engine import (
    build_learning_report,
    build_learning_signal,
    recommend_learning_action,
)
from revenex.outcome.tracking import (
    OutcomeEvaluation,
    OutcomeStatus,
)


def _evaluation(
    decision_id: str,
    signal: str,
    accuracy: float,
    variance: float,
    status: OutcomeStatus = OutcomeStatus.PARTIAL,
):
    return OutcomeEvaluation(
        decision_id=decision_id,
        status=status,
        collection_variance=variance,
        collection_accuracy=accuracy,
        exposure_variance=0.0,
        learning_signal=signal,
        evidence=(
            f"accuracy={accuracy}",
            f"variance={variance}",
        ),
    )


def test_learning_signal_captures_prediction_error():
    evaluation = _evaluation(
        "decision-1",
        "UNDERPREDICTED_COLLECTION",
        0.60,
        20000,
    )

    signal = build_learning_signal(evaluation)

    assert signal.decision_id == "decision-1"
    assert signal.signal == "UNDERPREDICTED_COLLECTION"
    assert 0 < signal.strength <= 1
    assert len(signal.evidence) == 2


def test_learning_report_detects_underprediction_bias():
    evaluations = (
        _evaluation(
            "d1",
            "UNDERPREDICTED_COLLECTION",
            0.60,
            20000,
        ),
        _evaluation(
            "d2",
            "UNDERPREDICTED_COLLECTION",
            0.70,
            15000,
        ),
        _evaluation(
            "d3",
            "PREDICTION_ALIGNED",
            0.95,
            1000,
        ),
    )

    report = build_learning_report(evaluations)

    assert report.evaluated_count == 3
    assert report.underprediction_count == 2
    assert report.overprediction_count == 0
    assert report.aligned_count == 1
    assert report.model_bias == "UNDERPREDICTING"


def test_learning_report_detects_overprediction_bias():
    evaluations = (
        _evaluation(
            "d1",
            "OVERPREDICTED_COLLECTION",
            0.50,
            -30000,
        ),
        _evaluation(
            "d2",
            "OVERPREDICTED_COLLECTION",
            0.60,
            -20000,
        ),
    )

    report = build_learning_report(evaluations)

    assert report.overprediction_count == 2
    assert report.model_bias == "OVERPREDICTING"


def test_learning_report_handles_insufficient_data():
    evaluation = OutcomeEvaluation(
        decision_id="d1",
        status=OutcomeStatus.INSUFFICIENT_DATA,
        collection_variance=None,
        collection_accuracy=None,
        exposure_variance=None,
        learning_signal="WAIT_FOR_OUTCOME",
        evidence=("missing actual outcome",),
    )

    report = build_learning_report((evaluation,))

    assert report.evaluation_count == 1
    assert report.evaluated_count == 0
    assert report.insufficient_data_count == 1
    assert report.learning_confidence == 0.0
    assert (
        recommend_learning_action(report)
        == "WAIT_FOR_MORE_OUTCOMES"
    )


def test_aligned_predictions_produce_aligned_learning_state():
    evaluations = (
        _evaluation(
            "d1",
            "PREDICTION_ALIGNED",
            0.98,
            500,
            OutcomeStatus.SUCCESS,
        ),
        _evaluation(
            "d2",
            "PREDICTION_ALIGNED",
            0.95,
            -500,
            OutcomeStatus.SUCCESS,
        ),
    )

    report = build_learning_report(evaluations)

    assert report.aligned_count == 2
    assert report.model_bias == "ALIGNED"
    assert report.average_collection_accuracy > 0.90
    assert (
        recommend_learning_action(report)
        == "MODEL_PERFORMANCE_ALIGNED"
    )


def test_learning_never_automatically_changes_model():
    evaluations = (
        _evaluation(
            "d1",
            "UNDERPREDICTED_COLLECTION",
            0.40,
            50000,
        ),
    )

    report = build_learning_report(evaluations)

    action = recommend_learning_action(report)

    assert action == "REVIEW_MODEL_UPWARD_CALIBRATION"

    # The report only recommends an action.
    # No model mutation or execution contract exists here.
    assert report.model_bias == "UNDERPREDICTING"
