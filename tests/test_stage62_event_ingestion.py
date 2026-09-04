
from revenex.events import (
    EventIngestionEngine,
    EventStore,
    build_event_audit,
    compute_signature,
    normalize_event,
    verify_signature,
)
from revenex.events.contracts import ProviderEvent


def test_signature_verification():

    secret = "test-secret"
    body = b'{"id":"pay-1"}'

    signature = compute_signature(
        secret,
        body,
    )

    assert verify_signature(
        secret,
        body,
        signature,
    )

    assert not verify_signature(
        secret,
        body,
        "bad-signature",
    )


def test_event_normalization():

    event = ProviderEvent(
        event_id="evt-1",
        provider="sandbox-recovery",
        event_type="payment.captured",
        occurred_at="2026-08-26T10:00:00Z",
        payload={
            "payment_id": "pay-1",
            "amount": 5000,
        },
        sandbox=True,
    )

    result = normalize_event(event)

    assert result.resource_type == "payment"
    assert result.resource_id == "pay-1"
    assert result.action == "captured"


def test_event_is_persisted():

    store = EventStore()

    engine = EventIngestionEngine(
        store=store
    )

    result = engine.ingest(
        event_id="evt-2",
        provider="sandbox-recovery",
        event_type="payment.captured",
        occurred_at="2026-08-26T10:00:00Z",
        payload={
            "payment_id": "pay-2",
            "amount": 10000,
        },
    )

    assert result.accepted is True
    assert result.duplicate is False
    assert result.status == "ACCEPTED"

    stored = store.get("evt-2")

    assert stored is not None
    assert stored["resource_type"] == "payment"
    assert stored["resource_id"] == "pay-2"

    store.close()


def test_duplicate_event_is_ignored():

    store = EventStore()

    engine = EventIngestionEngine(
        store=store
    )

    kwargs = dict(
        event_id="evt-duplicate",
        provider="sandbox-recovery",
        event_type="payment.captured",
        occurred_at="2026-08-26T10:00:00Z",
        payload={
            "payment_id": "pay-3",
        },
    )

    first = engine.ingest(**kwargs)
    second = engine.ingest(**kwargs)

    assert first.status == "ACCEPTED"
    assert second.status == "DUPLICATE_IGNORED"
    assert second.duplicate is True

    assert len(
        store.list_events()
    ) == 1

    store.close()


def test_invalid_signature_is_rejected():

    store = EventStore()

    engine = EventIngestionEngine(
        store=store,
        provider_secrets={
            "sandbox-recovery": "secret"
        },
    )

    result = engine.ingest(
        event_id="evt-invalid",
        provider="sandbox-recovery",
        event_type="payment.captured",
        occurred_at="2026-08-26T10:00:00Z",
        payload={
            "payment_id": "pay-4",
        },
        signature="wrong",
    )

    assert result.accepted is False
    assert result.status == "INVALID_SIGNATURE"

    assert store.get("evt-invalid") is None

    store.close()


def test_valid_signature_is_accepted():

    store = EventStore()

    engine = EventIngestionEngine(
        store=store,
        provider_secrets={
            "sandbox-recovery": "secret"
        },
    )

    payload = {
        "payment_id": "pay-5",
        "amount": 5000,
    }

    import json

    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = compute_signature(
        "secret",
        raw,
    )

    result = engine.ingest(
        event_id="evt-valid",
        provider="sandbox-recovery",
        event_type="payment.captured",
        occurred_at="2026-08-26T10:00:00Z",
        payload=payload,
        signature=signature,
        raw_body=raw,
    )

    assert result.accepted is True
    assert result.verified is True

    store.close()


def test_replay_is_read_only():

    store = EventStore()

    engine = EventIngestionEngine(
        store=store
    )

    engine.ingest(
        event_id="evt-replay",
        provider="sandbox-recovery",
        event_type="invoice.paid",
        occurred_at="2026-08-26T10:00:00Z",
        payload={
            "invoice_id": "inv-1",
        },
    )

    replay = engine.replay(
        "evt-replay"
    )

    assert replay is not None
    assert replay["replay_only"] is True
    assert replay["financial_mutation"] is False

    store.close()


def test_event_audit_preserves_safety():

    store = EventStore()

    engine = EventIngestionEngine(
        store=store
    )

    result = engine.ingest(
        event_id="evt-audit",
        provider="sandbox-recovery",
        event_type="refund.created",
        occurred_at="2026-08-26T10:00:00Z",
        payload={
            "refund_id": "ref-1",
        },
    )

    audit = build_event_audit(result)

    assert audit["accepted"] is True

    assert (
        audit["safety"]
        ["financial_mutation"]
        is False
    )

    assert (
        audit["safety"]
        ["provider_mutation"]
        is False
    )

    assert (
        audit["safety"]
        ["automatic_action"]
        is False
    )

    assert (
        audit["safety"]
        ["execution_allowed"]
        is False
    )

    store.close()
