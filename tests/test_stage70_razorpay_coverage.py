from revenex.coverage.razorpay import (
    coverage_summary,
)
from revenex.events.contracts import (
    normalize_revenue_event,
)
from revenex.payment_links.intelligence import (
    PaymentLinkState,
    analyze_payment_links,
)
from revenex.provider.capabilities import (
    ProviderCapability,
    RAZORPAY_CAPABILITIES,
)


def test_razorpay_coverage_complete():
    summary = coverage_summary()

    assert summary["provider"] == "razorpay"
    assert summary["coverage_percent"] == 100.0
    assert summary["read_only"] is True
    assert summary["financial_mutation"] is False
    assert summary["provider_mutation"] is False


def test_payment_link_paid():
    result = analyze_payment_links(
        [{
            "id": "plink_1",
            "amount": 100000,
            "amount_paid": 100000,
            "status": "paid",
        }]
    )[0]

    assert result.state == PaymentLinkState.PAID
    assert result.amount_remaining == 0
    assert result.collection_probability == 1.0
    assert result.read_only is True
    assert result.financial_mutation is False


def test_payment_link_partial():
    result = analyze_payment_links(
        [{
            "id": "plink_2",
            "amount": 100000,
            "amount_paid": 40000,
            "status": "partially_paid",
        }]
    )[0]

    assert result.state == PaymentLinkState.PARTIALLY_PAID
    assert result.amount_remaining == 60000
    assert result.collection_probability == 0.4


def test_provider_capabilities():
    assert RAZORPAY_CAPABILITIES.supports(
        ProviderCapability.PAYMENTS
    )
    assert RAZORPAY_CAPABILITIES.supports(
        ProviderCapability.PAYMENT_LINKS
    )
    assert RAZORPAY_CAPABILITIES.supports(
        ProviderCapability.WEBHOOKS
    )
    assert RAZORPAY_CAPABILITIES.supports(
        ProviderCapability.RECONCILIATION
    )
    assert RAZORPAY_CAPABILITIES.financial_mutation is False
    assert RAZORPAY_CAPABILITIES.provider_mutation is False


def test_event_normalization():
    event = normalize_revenue_event({
        "id": "evt_1",
        "event": "payment.captured",
        "created_at": 123,
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_1",
                    "amount": 100000,
                }
            }
        },
    })

    assert event.event_id == "evt_1"
    assert event.event_type == "payment.captured"
    assert event.entity_type == "payment"
    assert event.entity_id == "pay_1"
    assert event.payload_hash
    assert event.read_only is True
    assert event.financial_mutation is False
