
"""
REVENEX Phase 19 — Learning Intelligence.

Converts historical outcome intelligence into governed
learning recommendations.

This module DOES NOT:
- mutate models
- modify financial state
- call payment providers
- execute decisions

It only produces evidence-backed learning recommendations
for human review.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Iterable

from revenex.outcome.intelligence import (
    OutcomeIntelligence,
    OutcomeIntelligenceStatus,
    PredictionBias,
    aggregate_outcomes,
)


class LearningRecommendation(str, Enum):
    WAIT_FOR_MORE_OUTCOMES = "WAIT_FOR_MORE_OUTCOMES"
    REVIEW_MODEL_UPWARD_CALIBRATION = (
        "REVIEW_MODEL_UPWARD_CALIBRATION"
    )
    REVIEW_MODEL_DOWNWARD_CALIBRATION = (
        "REVIEW_MODEL_DOWNWARD_CALIBRATION"
    )
    MODEL_PERFORMANCE_ALIGNED = (
        "MODEL_PERFORMANCE_ALIGNED"
    )
    REVIEW_MODEL = "REVIEW_MODEL"


@dataclass(frozen=True)
class LearningDecision:
    recommendation: LearningRecommendation

    evaluated_count: int
    insufficient_data_count: int

    model_bias: PredictionBias
    learning_confidence: float

    average_collection_accuracy: float | None
    average_collection_variance: float | None
    average_exposure_variance: float | None

    rationale: tuple[str, ...]

    automatic_model_mutation: bool = False
    human_review_required: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


def build_learning_decision(
    evaluations: Iterable[OutcomeIntelligence],
) -> LearningDecision:

    evaluations = tuple(evaluations)
    report = aggregate_outcomes(evaluations)

    if report.evaluated_count == 0:
        return LearningDecision(
            recommendation=(
                LearningRecommendation.WAIT_FOR_MORE_OUTCOMES
            ),
            evaluated_count=report.evaluated_count,
            insufficient_data_count=(
                report.insufficient_data_count
            ),
            model_bias=report.model_bias,
            learning_confidence=(
                report.learning_confidence
            ),
            average_collection_accuracy=(
                report.average_collection_accuracy
            ),
            average_collection_variance=(
                report.average_collection_variance
            ),
            average_exposure_variance=(
                report.average_exposure_variance
            ),
            rationale=(
                "No evaluated real-world outcomes are available.",
                "More outcomes are required before model learning can be reviewed.",
            ),
        )

    # Do not recommend model calibration from a tiny sample.
    # Historical evidence must reach the minimum review threshold
    # before a directional learning recommendation is produced.
    MINIMUM_LEARNING_OUTCOMES = 3

    if report.evaluated_count < MINIMUM_LEARNING_OUTCOMES:
        return LearningDecision(
            recommendation=(
                LearningRecommendation.WAIT_FOR_MORE_OUTCOMES
            ),
            evaluated_count=report.evaluated_count,
            insufficient_data_count=(
                report.insufficient_data_count
            ),
            model_bias=report.model_bias,
            learning_confidence=(
                report.learning_confidence
            ),
            average_collection_accuracy=(
                report.average_collection_accuracy
            ),
            average_collection_variance=(
                report.average_collection_variance
            ),
            average_exposure_variance=(
                report.average_exposure_variance
            ),
            rationale=(
                "The number of evaluated outcomes is below the learning threshold.",
                f"At least {MINIMUM_LEARNING_OUTCOMES} evaluated outcomes are required.",
                "No model calibration recommendation will be produced yet.",
            ),
        )

    if (
        report.model_bias
        == PredictionBias.UNDERPREDICTING
    ):
        recommendation = (
            LearningRecommendation
            .REVIEW_MODEL_UPWARD_CALIBRATION
        )

        rationale = (
            "Observed collections are systematically above predictions.",
            "The model may be underpredicting collection performance.",
            "Human review should determine whether upward calibration is justified.",
        )

    elif (
        report.model_bias
        == PredictionBias.OVERPREDICTING
    ):
        recommendation = (
            LearningRecommendation
            .REVIEW_MODEL_DOWNWARD_CALIBRATION
        )

        rationale = (
            "Observed collections are systematically below predictions.",
            "The model may be overpredicting collection performance.",
            "Human review should determine whether downward calibration is justified.",
        )

    elif (
        report.model_bias
        == PredictionBias.ALIGNED
    ):
        recommendation = (
            LearningRecommendation
            .MODEL_PERFORMANCE_ALIGNED
        )

        rationale = (
            "Observed outcomes are broadly aligned with predictions.",
            "No calibration change is recommended from current evidence.",
        )

    else:
        recommendation = (
            LearningRecommendation.REVIEW_MODEL
        )

        rationale = (
            "Outcome evidence requires model review.",
        )

    if report.learning_confidence < 0.50:
        recommendation = (
            LearningRecommendation.WAIT_FOR_MORE_OUTCOMES
        )

        rationale = (
            *rationale,
            "Learning confidence is below the review threshold.",
            "Additional real-world outcomes should be collected.",
        )

    return LearningDecision(
        recommendation=recommendation,
        evaluated_count=report.evaluated_count,
        insufficient_data_count=(
            report.insufficient_data_count
        ),
        model_bias=report.model_bias,
        learning_confidence=(
            report.learning_confidence
        ),
        average_collection_accuracy=(
            report.average_collection_accuracy
        ),
        average_collection_variance=(
            report.average_collection_variance
        ),
        average_exposure_variance=(
            report.average_exposure_variance
        ),
        rationale=rationale,
    )


def learning_decision_to_dict(
    decision: LearningDecision,
) -> dict[str, Any]:

    payload = asdict(decision)

    payload["recommendation"] = (
        decision.recommendation.value
    )

    payload["model_bias"] = (
        decision.model_bias.value
    )

    payload["rationale"] = list(
        decision.rationale
    )

    return payload
