from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OutcomeEvaluation:
    status: str
    expected_value: float
    actual_value: float | None
    variance: float | None
    accuracy: float | None
    learning_signal: str
    learning_confidence: float
    explanation: str
    human_review_required: bool = True
    read_only: bool = True
    model_mutation: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class LearningLoopResult:
    evaluation: OutcomeEvaluation
    next_recommendation: str
    loop_state: str
    learning_ready: bool
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    model_mutation: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _confidence(value: Any) -> float:
    try:
        return min(max(float(value or 0), 0.0), 1.0)
    except (TypeError, ValueError):
        return 0.0


def _evaluate(
    expected: float,
    actual: Any,
) -> OutcomeEvaluation:
    if actual is None:
        return OutcomeEvaluation(
            status="INSUFFICIENT_DATA",
            expected_value=round(expected, 2),
            actual_value=None,
            variance=None,
            accuracy=None,
            learning_signal="WAIT_FOR_OUTCOME",
            learning_confidence=0.0,
            explanation=(
                "No actual real-world outcome is available. "
                "REVENEX will not infer or invent an outcome."
            ),
        )

    actual_value = _money(actual)
    variance = actual_value - expected

    if expected > 0:
        accuracy = max(
            0.0,
            min(
                1.0,
                1.0 - abs(variance) / expected,
            ),
        )
    else:
        accuracy = 1.0 if actual_value == 0 else 0.0

    if accuracy >= 0.90:
        signal = "PREDICTION_ACCURATE"
        confidence = accuracy
    elif accuracy >= 0.70:
        signal = "PREDICTION_ACCEPTABLE"
        confidence = accuracy
    else:
        signal = "PREDICTION_REVIEW_REQUIRED"
        confidence = accuracy

    return OutcomeEvaluation(
        status="EVALUATED",
        expected_value=round(expected, 2),
        actual_value=round(actual_value, 2),
        variance=round(variance, 2),
        accuracy=round(accuracy, 4),
        learning_signal=signal,
        learning_confidence=round(confidence, 4),
        explanation=(
            f"Expected ₹{expected:,.2f}; observed "
            f"₹{actual_value:,.2f}; variance "
            f"₹{variance:,.2f}; prediction accuracy "
            f"{accuracy:.2%}."
        ),
    )


def run_learning_loop(
    outcome: dict[str, Any] | None,
) -> LearningLoopResult:
    outcome = outcome or {}

    expected = _money(
        outcome.get("expected_value")
        or outcome.get("expected_collection")
    )

    actual = outcome.get("actual_value")

    if actual is None:
        actual = outcome.get("actual_collection")

    evaluation = _evaluate(
        expected,
        actual,
    )

    if evaluation.status == "INSUFFICIENT_DATA":
        next_recommendation = "WAIT_FOR_REAL_WORLD_OUTCOME"
        loop_state = "WAITING_FOR_OUTCOME"
        learning_ready = False
    elif evaluation.learning_signal == "PREDICTION_ACCURATE":
        next_recommendation = "REUSE_VALIDATED_SIGNAL_WITH_HUMAN_REVIEW"
        loop_state = "LEARNING_SIGNAL_READY"
        learning_ready = True
    elif evaluation.learning_signal == "PREDICTION_ACCEPTABLE":
        next_recommendation = "CONTINUE_MONITORING_WITH_HUMAN_REVIEW"
        loop_state = "LEARNING_SIGNAL_READY"
        learning_ready = True
    else:
        next_recommendation = "REVIEW_PREDICTION_ASSUMPTIONS"
        loop_state = "LEARNING_REVIEW_REQUIRED"
        learning_ready = True

    return LearningLoopResult(
        evaluation=evaluation,
        next_recommendation=next_recommendation,
        loop_state=loop_state,
        learning_ready=learning_ready,
    )
