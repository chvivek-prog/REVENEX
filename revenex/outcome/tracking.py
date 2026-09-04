"""
REVENEX Stage 39 — Outcome Tracking.

Records observed outcomes against previously generated
intelligence decisions.

This stage does not execute actions or mutate financial state.
"""

from dataclasses import dataclass
from enum import Enum


class OutcomeStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class OutcomeEvent:
    decision_id: str
    customer_id: str
    expected_collection: float
    actual_collection: float | None
    expected_remaining_exposure: float
    actual_remaining_exposure: float | None
    status: OutcomeStatus
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class OutcomeEvaluation:
    decision_id: str
    status: OutcomeStatus
    collection_variance: float | None
    collection_accuracy: float | None
    exposure_variance: float | None
    learning_signal: str
    evidence: tuple[str, ...]


def create_outcome_event(
    decision_id: str,
    customer_id: str,
    expected_collection: float,
    expected_remaining_exposure: float,
) -> OutcomeEvent:
    """Create a pending outcome record."""

    return OutcomeEvent(
        decision_id=str(decision_id),
        customer_id=str(customer_id),
        expected_collection=float(expected_collection),
        actual_collection=None,
        expected_remaining_exposure=float(
            expected_remaining_exposure
        ),
        actual_remaining_exposure=None,
        status=OutcomeStatus.PENDING,
        evidence=(
            "Outcome has not yet been observed.",
        ),
    )


def evaluate_outcome(
    outcome: OutcomeEvent,
) -> OutcomeEvaluation:
    """
    Compare expected and actual results.

    No actual result means the outcome cannot be evaluated.
    """

    if (
        outcome.actual_collection is None
        or outcome.actual_remaining_exposure is None
    ):
        return OutcomeEvaluation(
            decision_id=outcome.decision_id,
            status=OutcomeStatus.INSUFFICIENT_DATA,
            collection_variance=None,
            collection_accuracy=None,
            exposure_variance=None,
            learning_signal="WAIT_FOR_OUTCOME",
            evidence=(
                "Actual collection or remaining exposure is missing.",
            ),
        )

    expected = max(
        0.0,
        outcome.expected_collection,
    )

    actual = max(
        0.0,
        outcome.actual_collection,
    )

    collection_variance = actual - expected

    if expected > 0:
        collection_accuracy = max(
            0.0,
            1.0 - abs(collection_variance) / expected,
        )
    else:
        collection_accuracy = (
            1.0
            if actual == 0
            else 0.0
        )

    exposure_variance = (
        outcome.actual_remaining_exposure
        - outcome.expected_remaining_exposure
    )

    tolerance = max(
        1.0,
        expected * 0.10,
    )

    if abs(collection_variance) <= tolerance:
        status = OutcomeStatus.SUCCESS
        learning_signal = "PREDICTION_ALIGNED"
    elif actual > expected:
        status = OutcomeStatus.PARTIAL
        learning_signal = "UNDERPREDICTED_COLLECTION"
    else:
        status = OutcomeStatus.PARTIAL
        learning_signal = "OVERPREDICTED_COLLECTION"

    evidence = (
        f"expected_collection={expected:.2f}",
        f"actual_collection={actual:.2f}",
        f"collection_variance={collection_variance:.2f}",
        f"collection_accuracy={collection_accuracy:.4f}",
        f"exposure_variance={exposure_variance:.2f}",
    )

    return OutcomeEvaluation(
        decision_id=outcome.decision_id,
        status=status,
        collection_variance=collection_variance,
        collection_accuracy=collection_accuracy,
        exposure_variance=exposure_variance,
        learning_signal=learning_signal,
        evidence=evidence,
    )


def record_observed_outcome(
    pending: OutcomeEvent,
    actual_collection: float,
    actual_remaining_exposure: float,
) -> OutcomeEvent:
    """
    Create an immutable observed outcome from a pending event.
    """

    actual_collection = max(
        0.0,
        float(actual_collection),
    )

    actual_remaining_exposure = max(
        0.0,
        float(actual_remaining_exposure),
    )

    return OutcomeEvent(
        decision_id=pending.decision_id,
        customer_id=pending.customer_id,
        expected_collection=pending.expected_collection,
        actual_collection=actual_collection,
        expected_remaining_exposure=(
            pending.expected_remaining_exposure
        ),
        actual_remaining_exposure=(
            actual_remaining_exposure
        ),
        status=OutcomeStatus.SUCCESS,
        evidence=(
            "Observed outcome recorded.",
            f"actual_collection={actual_collection:.2f}",
            (
                "actual_remaining_exposure="
                f"{actual_remaining_exposure:.2f}"
            ),
        ),
    )
