import json

from revenex.event_infrastructure import (
    EventProcessor,
    EventStatus,
    EventStore,
    WebhookVerifier,
)


def payload():
    return {
        "id": "evt_stage23_1",
        "event": "payment.captured",
        "created_at": 123456,
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_123",
                    "amount": 100000,
                }
            }
        },
    }


def raw(payload):
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def test_signature_verification():
    verifier = WebhookVerifier("secret")

    signature = verifier.sign(
        b"hello"
    )

    assert verifier.verify(
        b"hello",
        signature,
    )

    assert not verifier.verify(
        b"tampered",
        signature,
    )


def test_event_ingestion():
    verifier = WebhookVerifier("secret")
    store = EventStore()
    processor = EventProcessor(
        store=store,
        verifier=verifier,
    )

    event_payload = payload()

    event = processor.ingest(
        payload=event_payload,
        signature=verifier.sign(
            raw(event_payload)
        ),
    )

    assert event.event_id == "evt_stage23_1"
    assert event.event_type == "payment.captured"
    assert event.entity_type == "payment"
    assert event.entity_id == "pay_123"
    assert event.status == EventStatus.VERIFIED
    assert event.signature_verified is True
    assert event.read_only is True
    assert event.financial_mutation is False
    assert event.provider_mutation is False

    store.close()


def test_duplicate_event_is_not_inserted_twice():
    verifier = WebhookVerifier("secret")
    store = EventStore()
    processor = EventProcessor(
        store=store,
        verifier=verifier,
    )

    event_payload = payload()
    signature = verifier.sign(
        raw(event_payload)
    )

    first = processor.ingest(
        payload=event_payload,
        signature=signature,
    )

    second = processor.ingest(
        payload=event_payload,
        signature=signature,
    )

    assert first.status == EventStatus.VERIFIED
    assert second.status == EventStatus.DUPLICATE

    stored = store.get(
        "evt_stage23_1"
    )

    assert stored is not None
    assert stored.status == EventStatus.VERIFIED

    store.close()


def test_invalid_signature_is_rejected():
    verifier = WebhookVerifier("secret")
    store = EventStore()
    processor = EventProcessor(
        store=store,
        verifier=verifier,
    )

    event = processor.ingest(
        payload=payload(),
        signature="invalid",
    )

    assert event.status == EventStatus.REJECTED
    assert event.signature_verified is False

    store.close()


def test_processing_lifecycle():
    verifier = WebhookVerifier("secret")
    store = EventStore()
    processor = EventProcessor(
        store=store,
        verifier=verifier,
    )

    event_payload = payload()

    processor.ingest(
        payload=event_payload,
        signature=verifier.sign(
            raw(event_payload)
        ),
    )

    processing = processor.mark_processing(
        "evt_stage23_1"
    )

    assert processing.status == EventStatus.PROCESSING
    assert processing.attempt_count == 1

    processed = processor.mark_processed(
        "evt_stage23_1"
    )

    assert processed.status == EventStatus.PROCESSED

    store.close()


def test_failed_processing_lifecycle():
    verifier = WebhookVerifier("secret")
    store = EventStore()
    processor = EventProcessor(
        store=store,
        verifier=verifier,
    )

    event_payload = payload()

    processor.ingest(
        payload=event_payload,
        signature=verifier.sign(
            raw(event_payload)
        ),
    )

    processor.mark_processing(
        "evt_stage23_1"
    )

    failed = processor.mark_failed(
        "evt_stage23_1"
    )

    assert failed.status == EventStatus.FAILED
    assert failed.read_only is True
    assert failed.financial_mutation is False
    assert failed.provider_mutation is False

    store.close()


def test_event_persistence_survives_store_reopen():
    import sqlite3

    connection = sqlite3.connect(":memory:")
    verifier = WebhookVerifier("secret")
    store = EventStore(connection)
    processor = EventProcessor(
        store=store,
        verifier=verifier,
    )

    event_payload = payload()

    processor.ingest(
        payload=event_payload,
        signature=verifier.sign(
            raw(event_payload)
        ),
    )

    restored = store.get(
        "evt_stage23_1"
    )

    assert restored is not None
    assert restored.event_type == "payment.captured"

    store.close()
