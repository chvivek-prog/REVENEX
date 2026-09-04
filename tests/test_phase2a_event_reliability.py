from revenex.phase2a import (
    EventReliabilityStatus,
    classify_event_reliability,
)


def test_valid_event_is_accepted():
    result = classify_event_reliability(
        {"event_id": "evt-1", "sequence": 10}
    )
    assert result.status == EventReliabilityStatus.ACCEPTED
    assert result.ordered is True
    assert result.human_review_required is False


def test_duplicate_event_is_detected():
    result = classify_event_reliability(
        {"event_id": "evt-1", "sequence": 10},
        seen_event_ids={"evt-1"},
    )
    assert result.status == EventReliabilityStatus.DUPLICATE
    assert result.duplicate is True
    assert result.replay is True


def test_missing_event_id_requires_review():
    result = classify_event_reliability(
        {"sequence": 10}
    )
    assert result.status == EventReliabilityStatus.INVALID
    assert result.human_review_required is True


def test_invalid_signature_is_rejected():
    result = classify_event_reliability(
        {"event_id": "evt-invalid", "signature_valid": False}
    )
    assert result.status == EventReliabilityStatus.INVALID
    assert result.human_review_required is True


def test_out_of_order_event_is_detected():
    result = classify_event_reliability(
        {"event_id": "evt-old", "sequence": 9},
        previous_sequence=10,
    )
    assert result.status == EventReliabilityStatus.OUT_OF_ORDER
    assert result.ordered is False
    assert result.human_review_required is True


def test_malformed_sequence_requires_review():
    result = classify_event_reliability(
        {"event_id": "evt-review", "sequence": "not-a-number"}
    )
    assert result.status == EventReliabilityStatus.REVIEW
    assert result.human_review_required is True


def test_reliability_layer_is_always_read_only():
    result = classify_event_reliability(
        {"event_id": "evt-safe"}
    )
    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False


def test_replay_flag_is_preserved():
    result = classify_event_reliability(
        {"event_id": "evt-replay", "replay": True}
    )
    assert result.replay is True
