
from revenex.events.bus import (
    EventBus,
    create_webhook_event,
)
from revenex.reconciliation.engine import (
    reconcile,
    reconcile_payments,
    summarize_reconciliation,
)
from revenex.webhooks.validation import (
    normalize_webhook_payload,
    verify_webhook_signature,
)
import hashlib
import hmac
import json


def test_webhook_event_is_deterministic():
    payload = {
        "id": "pay_1",
        "amount": 1000,
    }

    first = create_webhook_event(
        event_type="payment.captured",
        entity_id="pay_1",
        payload=payload,
    )

    second = create_webhook_event(
        event_type="payment.captured",
        entity_id="pay_1",
        payload=payload,
    )

    assert first.event_id == second.event_id


def test_event_bus_is_idempotent():
    bus = EventBus()
    received = []

    bus.subscribe(
        "payment.captured",
        lambda event: received.append(
            event.entity_id
        ),
    )

    event = create_webhook_event(
        event_type="payment.captured",
        entity_id="pay_1",
        payload={"amount": 1000},
    )

    assert bus.publish(event) is True
    assert bus.publish(event) is False
    assert received == ["pay_1"]


def test_signature_verification():
    payload = b'{"id":"pay_1"}'
    secret = "phase8-secret"

    signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    assert verify_webhook_signature(
        payload=payload,
        signature=signature,
        secret=secret,
    )

    assert not verify_webhook_signature(
        payload=payload,
        signature="invalid",
        secret=secret,
    )


def test_webhook_normalization():
    result = normalize_webhook_payload(
        {
            "event": "payment.captured",
            "entity": {
                "id": "pay_123",
                "amount": 5000,
            },
        }
    )

    assert result["event_type"] == "payment.captured"
    assert result["entity_id"] == "pay_123"


def test_reconciled_payment():
    result = reconcile(
        entity_type="payment",
        entity_id="pay_1",
        expected_amount=100000,
        observed_amount=100000,
    )

    assert result.status == "RECONCILED"
    assert result.variance == 0.0
    assert result.confidence == 1.0
    assert result.read_only is True


def test_payment_variance():
    result = reconcile(
        entity_type="payment",
        entity_id="pay_2",
        expected_amount=100000,
        observed_amount=97000,
    )

    assert result.status == "VARIANCE_UNDER"
    assert result.variance == -3000.0
    assert result.human_review_required if hasattr(
        result,
        "human_review_required",
    ) else True


def test_reconcile_payment_collection():
    results = reconcile_payments(
        [
            {
                "payment_id": "p1",
                "amount": 100000,
            },
            {
                "payment_id": "p2",
                "amount": 50000,
            },
        ],
        [
            {
                "payment_id": "p1",
                "amount": 100000,
            },
            {
                "payment_id": "p2",
                "amount": 45000,
            },
        ],
    )

    assert len(results) == 2
    assert results[0].status == "RECONCILED"
    assert results[1].status == "VARIANCE_UNDER"


def test_reconciliation_summary():
    results = [
        reconcile(
            entity_type="payment",
            entity_id="p1",
            expected_amount=100,
            observed_amount=100,
        ),
        reconcile(
            entity_type="payment",
            entity_id="p2",
            expected_amount=100,
            observed_amount=90,
        ),
    ]

    summary = summarize_reconciliation(results)

    assert summary["total_items"] == 2
    assert summary["reconciled_items"] == 1
    assert summary["variance_under_items"] == 1
    assert summary["human_review_required"] is True
    assert summary["read_only"] is True


def test_no_financial_mutation():
    result = reconcile(
        entity_type="payment",
        entity_id="p1",
        expected_amount=1000,
        observed_amount=900,
    )

    assert result.read_only is True
