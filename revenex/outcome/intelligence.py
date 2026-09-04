
"""
REVENEX Phase 18 — Outcome Intelligence.

Transforms individual prediction-vs-actual evaluations into
structured outcome intelligence.

Pipeline:

Prediction
    ↓
Real-world Outcome
    ↓
Variance
    ↓
Accuracy
    ↓
Bias
    ↓
Learning Signal

No model mutation.
No financial mutation.
No provider mutation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Iterable


class OutcomeIntelligenceStatus(str, Enum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    EVALUATED = "EVALUATED"


class PredictionBias(str, Enum):
    ALIGNED = "ALIGNED"
    UNDERPREDICTING = "UNDERPREDICTING"
    OVERPREDICTING = "OVERPREDICTING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class OutcomeRecord:
    decision_id: str
    expected_collection: float
    actual_collection: float | None
    expected_remaining_exposure: float
    actual_remaining_exposure: float | None


@dataclass(frozen=True)
class OutcomeIntelligence:
    decision_id: str
    status: OutcomeIntelligenceStatus

    expected_collection: float
    actual_collection: float | None

    collection_variance: float | None
    collection_accuracy: float | None

    expected_remaining_exposure: float
    actual_remaining_exposure: float | None
    exposure_variance: float | None

    prediction_bias: PredictionBias
    learning_signal: str

    evidence: tuple[str, ...]

    automatic_model_mutation: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False
    human_review_required: bool = True


@dataclass(frozen=True)
class OutcomeAggregate:
    evaluated_count: int
    insufficient_data_count: int

    average_collection_accuracy: float | None
    average_collection_variance: float | None
    average_exposure_variance: float | None

    aligned_count: int
    underpredicting_count: int
    overpredicting_count: int

    model_bias: PredictionBias
    learning_confidence: float

    evidence: tuple[str, ...]

    automatic_model_mutation: bool = False
    human_review_required: bool = True


def _accuracy(
    expected: float,
    actual: float,
) -> float:

    expected = max(0.0, float(expected))
    actual = max(0.0, float(actual))

    if expected == 0:
        return 1.0 if actual == 0 else 0.0

    return max(
        0.0,
        1.0 - abs(actual - expected) / expected,
    )


def _bias(
    expected: float,
    actual: float,
) -> PredictionBias:

    expected = max(0.0, float(expected))
    actual = max(0.0, float(actual))

    # Keep the alignment band strictly below 10%.
    # An exact 10% deviation is therefore treated as a
    # meaningful directional prediction error.
    tolerance = max(
        1.0,
        expected * 0.10,
    )

    variance = actual - expected

    if abs(variance) < tolerance:
        return PredictionBias.ALIGNED

    if actual > expected:
        return PredictionBias.UNDERPREDICTING

    return PredictionBias.OVERPREDICTING


def evaluate_outcome_intelligence(
    outcome: OutcomeRecord,
) -> OutcomeIntelligence:

    expected = max(
        0.0,
        float(outcome.expected_collection),
    )

    expected_exposure = max(
        0.0,
        float(
            outcome.expected_remaining_exposure
        ),
    )

    if (
        outcome.actual_collection is None
        or outcome.actual_remaining_exposure is None
    ):
        return OutcomeIntelligence(
            decision_id=outcome.decision_id,
            status=(
                OutcomeIntelligenceStatus.INSUFFICIENT_DATA
            ),
            expected_collection=expected,
            actual_collection=None,
            collection_variance=None,
            collection_accuracy=None,
            expected_remaining_exposure=expected_exposure,
            actual_remaining_exposure=None,
            exposure_variance=None,
            prediction_bias=(
                PredictionBias.INSUFFICIENT_DATA
            ),
            learning_signal="WAIT_FOR_OUTCOME",
            evidence=(
                "Actual collection is required.",
                "Actual remaining exposure is required.",
                "Prediction accuracy cannot yet be evaluated.",
            ),
        )

    actual = max(
        0.0,
        float(outcome.actual_collection),
    )

    actual_exposure = max(
        0.0,
        float(
            outcome.actual_remaining_exposure
        ),
    )

    collection_variance = actual - expected
    exposure_variance = (
        actual_exposure - expected_exposure
    )

    accuracy = _accuracy(
        expected,
        actual,
    )

    bias = _bias(
        expected,
        actual,
    )

    if bias == PredictionBias.ALIGNED:
        signal = "PREDICTION_ALIGNED"
    elif bias == PredictionBias.UNDERPREDICTING:
        signal = "UNDERPREDICTED_COLLECTION"
    else:
        signal = "OVERPREDICTED_COLLECTION"

    evidence = (
        f"expected_collection={expected:.2f}",
        f"actual_collection={actual:.2f}",
        f"collection_variance={collection_variance:.2f}",
        f"collection_accuracy={accuracy:.4f}",
        f"expected_remaining_exposure={expected_exposure:.2f}",
        f"actual_remaining_exposure={actual_exposure:.2f}",
        f"exposure_variance={exposure_variance:.2f}",
        f"prediction_bias={bias.value}",
    )

    return OutcomeIntelligence(
        decision_id=outcome.decision_id,
        status=OutcomeIntelligenceStatus.EVALUATED,
        expected_collection=expected,
        actual_collection=actual,
        collection_variance=collection_variance,
        collection_accuracy=accuracy,
        expected_remaining_exposure=expected_exposure,
        actual_remaining_exposure=actual_exposure,
        exposure_variance=exposure_variance,
        prediction_bias=bias,
        learning_signal=signal,
        evidence=evidence,
    )


def aggregate_outcomes(
    evaluations: Iterable[OutcomeIntelligence],
) -> OutcomeAggregate:

    evaluated = [
        item
        for item in evaluations
        if item.status
        == OutcomeIntelligenceStatus.EVALUATED
    ]

    insufficient = [
        item
        for item in evaluations
        if item.status
        == OutcomeIntelligenceStatus.INSUFFICIENT_DATA
    ]

    if not evaluated:
        return OutcomeAggregate(
            evaluated_count=0,
            insufficient_data_count=len(insufficient),
            average_collection_accuracy=None,
            average_collection_variance=None,
            average_exposure_variance=None,
            aligned_count=0,
            underpredicting_count=0,
            overpredicting_count=0,
            model_bias=PredictionBias.INSUFFICIENT_DATA,
            learning_confidence=0.0,
            evidence=(
                "No evaluated real-world outcomes are available.",
                "Collect additional outcomes before assessing model bias.",
            ),
        )

    accuracies = [
        float(item.collection_accuracy or 0.0)
        for item in evaluated
    ]

    collection_variances = [
        float(item.collection_variance or 0.0)
        for item in evaluated
    ]

    exposure_variances = [
        float(item.exposure_variance or 0.0)
        for item in evaluated
    ]

    aligned = sum(
        item.prediction_bias
        == PredictionBias.ALIGNED
        for item in evaluated
    )

    under = sum(
        item.prediction_bias
        == PredictionBias.UNDERPREDICTING
        for item in evaluated
    )

    over = sum(
        item.prediction_bias
        == PredictionBias.OVERPREDICTING
        for item in evaluated
    )

    counts = {
        PredictionBias.ALIGNED: aligned,
        PredictionBias.UNDERPREDICTING: under,
        PredictionBias.OVERPREDICTING: over,
    }

    dominant_bias = max(
        counts,
        key=counts.get,
    )

    dominance = (
        counts[dominant_bias]
        / len(evaluated)
    )

    learning_confidence = min(
        1.0,
        (
            (len(evaluated) / 10.0)
            * 0.5
        )
        + (
            dominance * 0.5
        ),
    )

    return OutcomeAggregate(
        evaluated_count=len(evaluated),
        insufficient_data_count=len(insufficient),
        average_collection_accuracy=(
            sum(accuracies)
            / len(accuracies)
        ),
        average_collection_variance=(
            sum(collection_variances)
            / len(collection_variances)
        ),
        average_exposure_variance=(
            sum(exposure_variances)
            / len(exposure_variances)
        ),
        aligned_count=aligned,
        underpredicting_count=under,
        overpredicting_count=over,
        model_bias=dominant_bias,
        learning_confidence=learning_confidence,
        evidence=(
            f"evaluated_count={len(evaluated)}",
            f"insufficient_data_count={len(insufficient)}",
            f"aligned_count={aligned}",
            f"underpredicting_count={under}",
            f"overpredicting_count={over}",
            f"dominant_bias={dominant_bias.value}",
            f"learning_confidence={learning_confidence:.4f}",
        ),
    )


def outcome_to_dict(
    outcome: OutcomeIntelligence,
) -> dict[str, Any]:

    payload = asdict(outcome)

    payload["status"] = (
        outcome.status.value
    )

    payload["prediction_bias"] = (
        outcome.prediction_bias.value
    )

    payload["evidence"] = list(
        outcome.evidence
    )

    return payload


def aggregate_to_dict(
    aggregate: OutcomeAggregate,
) -> dict[str, Any]:

    payload = asdict(aggregate)

    payload["model_bias"] = (
        aggregate.model_bias.value
    )

    payload["evidence"] = list(
        aggregate.evidence
    )

    return payload
