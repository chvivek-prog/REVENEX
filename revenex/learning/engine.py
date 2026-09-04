"""
REVENEX Stage 40 — Learning Engine.

Transforms evaluated outcomes into deterministic learning signals
and aggregate model-quality metrics.

This stage does not automatically change production model weights.
It creates auditable learning evidence for future model updates.
"""

from dataclasses import dataclass

from revenex.outcome.tracking import (
    OutcomeEvaluation,
    OutcomeStatus,
)


@dataclass(frozen=True)
class LearningSignal:
    decision_id: str
    signal: str
    strength: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class LearningReport:
    evaluation_count: int
    evaluated_count: int
    insufficient_data_count: int

    success_count: int
    partial_count: int

    average_collection_accuracy: float
    average_collection_variance: float

    underprediction_count: int
    overprediction_count: int
    aligned_count: int

    model_bias: str
    learning_confidence: float

    signals: tuple[LearningSignal, ...]


def _signal_strength(
    evaluation: OutcomeEvaluation,
) -> float:
    accuracy = evaluation.collection_accuracy

    if accuracy is None:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            1.0 - accuracy,
        ),
    )


def build_learning_signal(
    evaluation: OutcomeEvaluation,
) -> LearningSignal:
    """
    Convert one evaluated outcome into an auditable signal.
    """

    if evaluation.status == OutcomeStatus.INSUFFICIENT_DATA:
        return LearningSignal(
            decision_id=evaluation.decision_id,
            signal="WAIT_FOR_OUTCOME",
            strength=0.0,
            evidence=evaluation.evidence,
        )

    return LearningSignal(
        decision_id=evaluation.decision_id,
        signal=evaluation.learning_signal,
        strength=_signal_strength(evaluation),
        evidence=evaluation.evidence,
    )


def build_learning_report(
    evaluations: tuple[OutcomeEvaluation, ...],
) -> LearningReport:
    """
    Aggregate historical evaluations into model-quality evidence.
    """

    evaluation_count = len(evaluations)

    insufficient = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.status == OutcomeStatus.INSUFFICIENT_DATA
    )

    evaluated = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.status != OutcomeStatus.INSUFFICIENT_DATA
    )

    success_count = sum(
        1
        for evaluation in evaluated
        if evaluation.status == OutcomeStatus.SUCCESS
    )

    partial_count = sum(
        1
        for evaluation in evaluated
        if evaluation.status == OutcomeStatus.PARTIAL
    )

    accuracies = tuple(
        evaluation.collection_accuracy
        for evaluation in evaluated
        if evaluation.collection_accuracy is not None
    )

    variances = tuple(
        evaluation.collection_variance
        for evaluation in evaluated
        if evaluation.collection_variance is not None
    )

    average_accuracy = (
        sum(accuracies) / len(accuracies)
        if accuracies
        else 0.0
    )

    average_variance = (
        sum(variances) / len(variances)
        if variances
        else 0.0
    )

    underprediction_count = sum(
        1
        for evaluation in evaluated
        if evaluation.learning_signal
        == "UNDERPREDICTED_COLLECTION"
    )

    overprediction_count = sum(
        1
        for evaluation in evaluated
        if evaluation.learning_signal
        == "OVERPREDICTED_COLLECTION"
    )

    aligned_count = sum(
        1
        for evaluation in evaluated
        if evaluation.learning_signal
        == "PREDICTION_ALIGNED"
    )

    if underprediction_count > overprediction_count:
        model_bias = "UNDERPREDICTING"
    elif overprediction_count > underprediction_count:
        model_bias = "OVERPREDICTING"
    elif aligned_count:
        model_bias = "ALIGNED"
    else:
        model_bias = "UNKNOWN"

    learning_confidence = (
        min(
            1.0,
            0.30
            + min(0.50, len(evaluated) * 0.05)
            + (average_accuracy * 0.20),
        )
        if evaluated
        else 0.0
    )

    signals = tuple(
        build_learning_signal(evaluation)
        for evaluation in evaluations
    )

    return LearningReport(
        evaluation_count=evaluation_count,
        evaluated_count=len(evaluated),
        insufficient_data_count=len(insufficient),
        success_count=success_count,
        partial_count=partial_count,
        average_collection_accuracy=average_accuracy,
        average_collection_variance=average_variance,
        underprediction_count=underprediction_count,
        overprediction_count=overprediction_count,
        aligned_count=aligned_count,
        model_bias=model_bias,
        learning_confidence=learning_confidence,
        signals=signals,
    )


def recommend_learning_action(
    report: LearningReport,
) -> str:
    """
    Produce an advisory learning recommendation.

    No model is automatically modified.
    """

    if report.evaluated_count == 0:
        return "WAIT_FOR_MORE_OUTCOMES"

    # Strong directional evidence takes precedence over the
    # aggregate confidence threshold. A detected systematic
    # bias is actionable learning evidence even with a small
    # sample size; it remains advisory and cannot mutate a model.

    if report.model_bias == "UNDERPREDICTING":
        return "REVIEW_MODEL_UPWARD_CALIBRATION"

    if report.model_bias == "OVERPREDICTING":
        return "REVIEW_MODEL_DOWNWARD_CALIBRATION"

    if report.learning_confidence < 0.50:
        return "COLLECT_MORE_OUTCOMES"

    if report.model_bias == "ALIGNED":
        return "MODEL_PERFORMANCE_ALIGNED"

    return "REVIEW_MODEL"
