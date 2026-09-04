
from revenex.learning.intelligence import (
    LearningRecommendation,
    build_learning_decision,
)
from revenex.outcome.intelligence import (
    OutcomeRecord,
    evaluate_outcome_intelligence,
)


def evaluation(
    decision_id,
    expected,
    actual,
):
    return evaluate_outcome_intelligence(
        OutcomeRecord(
            decision_id=decision_id,
            expected_collection=expected,
            actual_collection=actual,
            expected_remaining_exposure=10000,
            actual_remaining_exposure=10000,
        )
    )


def test_no_outcomes_waits():

    result = build_learning_decision([])

    assert (
        result.recommendation
        == LearningRecommendation.WAIT_FOR_MORE_OUTCOMES
    )

    assert result.evaluated_count == 0
    assert result.learning_confidence == 0.0


def test_underprediction_generates_upward_review():

    evaluations = [
        evaluation("u1", 100000, 120000),
        evaluation("u2", 100000, 115000),
        evaluation("u3", 100000, 130000),
    ]

    result = build_learning_decision(
        evaluations
    )

    assert (
        result.recommendation
        == LearningRecommendation
        .REVIEW_MODEL_UPWARD_CALIBRATION
    )

    assert result.model_bias.value == "UNDERPREDICTING"


def test_overprediction_generates_downward_review():

    evaluations = [
        evaluation("o1", 100000, 70000),
        evaluation("o2", 100000, 75000),
        evaluation("o3", 100000, 60000),
    ]

    result = build_learning_decision(
        evaluations
    )

    assert (
        result.recommendation
        == LearningRecommendation
        .REVIEW_MODEL_DOWNWARD_CALIBRATION
    )

    assert result.model_bias.value == "OVERPREDICTING"


def test_aligned_model_is_not_mutated():

    evaluations = [
        evaluation("a1", 100000, 100000),
        evaluation("a2", 100000, 102000),
        evaluation("a3", 100000, 98000),
    ]

    result = build_learning_decision(
        evaluations
    )

    assert (
        result.recommendation
        == LearningRecommendation
        .MODEL_PERFORMANCE_ALIGNED
    )


def test_low_confidence_waits_for_more_outcomes():

    result = build_learning_decision(
        [
            evaluation(
                "single",
                100000,
                130000,
            )
        ]
    )

    assert (
        result.recommendation
        == LearningRecommendation
        .WAIT_FOR_MORE_OUTCOMES
    )


def test_governance_never_allows_mutation():

    result = build_learning_decision(
        [
            evaluation("g1", 100000, 120000),
            evaluation("g2", 100000, 125000),
            evaluation("g3", 100000, 130000),
            evaluation("g4", 100000, 120000),
            evaluation("g5", 100000, 125000),
            evaluation("g6", 100000, 130000),
            evaluation("g7", 100000, 120000),
            evaluation("g8", 100000, 125000),
            evaluation("g9", 100000, 130000),
            evaluation("g10", 100000, 120000),
        ]
    )

    assert result.automatic_model_mutation is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False
    assert result.human_review_required is True
