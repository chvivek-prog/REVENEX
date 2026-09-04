
from revenex.api.revenue_intelligence import analyze_revenue
from revenex.order.intelligence import (
    build_order_intelligence,
    summarize_order_behavior,
)
from revenex.subscription.intelligence import (
    build_subscription_intelligence,
    summarize_subscription_behavior,
)


def test_order_intelligence_paid():
    result = build_order_intelligence(
        [
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
                "amount": 100000,
                "amount_paid": 100000,
                "status": "paid",
            }
        ]
    )

    assert len(result) == 1

    order = result[0]

    assert order["order_id"] == "order-1"
    assert order["has_successful_payment"] is True
    assert order["order_signal"] == "ORDER_REALIZED"
    assert order["realization_ratio"] == 1.0
    assert order["read_only"] is True


def test_order_failed():
    result = build_order_intelligence(
        [
            {
                "order_id": "order-failed",
                "customer_id": "customer-1",
                "amount": 100000,
                "status": "failed",
            }
        ]
    )

    order = result[0]

    assert order["risk_level"] == "HIGH"
    assert order["order_signal"] == "ORDER_FAILURE_PRESSURE"


def test_order_summary():
    result = build_order_intelligence(
        [
            {
                "order_id": "order-1",
                "amount": 100000,
                "amount_paid": 100000,
                "status": "paid",
            },
            {
                "order_id": "order-2",
                "amount": 50000,
                "amount_paid": 0,
                "status": "failed",
            },
        ]
    )

    summary = summarize_order_behavior(result)

    assert summary["total_orders"] == 2
    assert summary["realized_orders"] == 1
    assert summary["failed_orders"] == 1
    assert summary["order_value"] == 150000.0
    assert summary["realized_value"] == 100000.0
    assert summary["read_only"] is True


def test_subscription_active():
    result = build_subscription_intelligence(
        [
            {
                "subscription_id": "sub-1",
                "customer_id": "customer-1",
                "status": "active",
                "plan_amount": 10000,
                "paid_count": 3,
                "total_count": 12,
            }
        ]
    )

    assert len(result) == 1

    subscription = result[0]

    assert subscription["subscription_id"] == "sub-1"
    assert subscription["renewal_risk"] == "LOW"
    assert subscription["remaining_cycles"] == 9
    assert subscription["recurring_revenue_exposure"] == 90000.0
    assert subscription["read_only"] is True


def test_subscription_at_risk():
    result = build_subscription_intelligence(
        [
            {
                "subscription_id": "sub-risk",
                "customer_id": "customer-1",
                "status": "halted",
                "plan_amount": 20000,
                "paid_count": 2,
                "total_count": 6,
            }
        ]
    )

    subscription = result[0]

    assert subscription["renewal_risk"] == "HIGH"
    assert subscription["subscription_signal"] == "SUBSCRIPTION_AT_RISK"


def test_subscription_summary():
    result = build_subscription_intelligence(
        [
            {
                "subscription_id": "sub-1",
                "status": "active",
                "plan_amount": 10000,
                "paid_count": 3,
                "total_count": 12,
            },
            {
                "subscription_id": "sub-2",
                "status": "halted",
                "plan_amount": 20000,
                "paid_count": 2,
                "total_count": 6,
            },
        ]
    )

    summary = summarize_subscription_behavior(result)

    assert summary["total_subscriptions"] == 2
    assert summary["active_subscriptions"] == 1
    assert summary["at_risk_subscriptions"] == 1
    assert summary["recurring_revenue_exposure"] == 170000.0
    assert summary["read_only"] is True


def test_api_contains_phase4_fields():
    response = analyze_revenue(
        [
            {
                "invoice_id": "inv-1",
                "customer_id": "customer-1",
                "amount": 100000,
                "outstanding_amount": 50000,
                "days_overdue": 30,
                "order_id": "order-1",
                "subscription_id": "sub-1",
            }
        ],
        [
            {
                "payment_id": "pay-1",
                "customer_id": "customer-1",
                "invoice_id": "inv-1",
                "order_id": "order-1",
                "amount": 50000,
                "status": "captured",
            }
        ],
        decision_id="phase4-api-test",
    )

    assert hasattr(response, "orders")
    assert hasattr(response, "subscriptions")
    assert hasattr(response, "order_summary")
    assert hasattr(response, "subscription_summary")

    assert response.safety["execution_allowed"] is False
    assert response.safety["automatic_action"] is False
    assert response.safety["financial_mutation"] is False
    assert response.safety["provider_mutation"] is False
