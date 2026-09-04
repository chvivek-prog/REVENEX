from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EventReliabilityStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    INVALID = "INVALID"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class EventReliabilityRecord:
    event_id: str
    status: EventReliabilityStatus
    duplicate: bool
    replay: bool
    ordered: bool
    human_review_required: bool
    read_only: bool
    financial_mutation: bool
    provider_mutation: bool
    execution_allowed: bool


def classify_event_reliability(
    event: dict[str, Any],
    *,
    seen_event_ids: set[str] | frozenset[str] = frozenset(),
    previous_sequence: int | None = None,
) -> EventReliabilityRecord:
    event_id = str(event.get("event_id") or event.get("id") or "").strip()

    if not event_id:
        return EventReliabilityRecord(
            event_id="",
            status=EventReliabilityStatus.INVALID,
            duplicate=False,
            replay=False,
            ordered=False,
            human_review_required=True,
            read_only=True,
            financial_mutation=False,
            provider_mutation=False,
            execution_allowed=False,
        )

    duplicate = event_id in seen_event_ids

    sequence_value = event.get("sequence")
    sequence: int | None = None
    if sequence_value is not None:
        try:
            sequence = int(sequence_value)
        except (TypeError, ValueError):
            sequence = None

    out_of_order = (
        previous_sequence is not None
        and sequence is not None
        and sequence < previous_sequence
    )

    replay = duplicate or bool(event.get("replay", False))

    if duplicate:
        status = EventReliabilityStatus.DUPLICATE
    elif out_of_order:
        status = EventReliabilityStatus.OUT_OF_ORDER
    elif event.get("signature_valid") is False:
        status = EventReliabilityStatus.INVALID
    elif sequence_value is not None and sequence is None:
        status = EventReliabilityStatus.REVIEW
    else:
        status = EventReliabilityStatus.ACCEPTED

    review = status in {
        EventReliabilityStatus.INVALID,
        EventReliabilityStatus.OUT_OF_ORDER,
        EventReliabilityStatus.REVIEW,
    }

    return EventReliabilityRecord(
        event_id=event_id,
        status=status,
        duplicate=duplicate,
        replay=replay,
        ordered=not out_of_order,
        human_review_required=review,
        read_only=True,
        financial_mutation=False,
        provider_mutation=False,
        execution_allowed=False,
    )
