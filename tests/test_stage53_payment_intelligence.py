
from revenex.api.revenue_intelligence import analyze_revenue
from revenex.payment.intelligence import (
    build_payment_intelligence,
    summarize_payment_behavior,
)


def test_payment_intelligence_success():
    result = build_payment_intelligence(
        [
            {
                "payment_id": "pay-1",
                "customer_id": "customer-47",
                "invoice_id": "inv-1",
                "amount": 100000,
                "status": "captured",
            }
        ],
        [
            {
                "invoice_id": "inv-1",
                "amount": 150000,
                "outstanding_amount": 150000,
            }
        ],
    )

    assert len(result) == 1

    payment = result[0]

    assert payment["payment_id"] == "pay-1"
    assert payment["customer_id"] == "customer-47"
    assert payment["invoice_id"] == "inv-1"
    assert payment["amount"] == 100000.0
    assert payment["successful"] is True
    assert payment["failed"] is False
    assert payment["payment_signal"] == "PAYMENT_REALIZED"
    assert payment["payment_coverage"] > 0
    assert payment["read_only"] is True


def test_failed_payment_is_high_risk():
    result = build_payment_intelligence(
        [
            {
                "payment_id": "pay-failed",
                "customer_id": "customer-1",
                "amount": 50000,
                "status": "failed",
            }
        ]
    )

    payment = result[0]

    assert payment["failed"] is True
    assert payment["successful"] is False
    assert payment["risk_level"] == "HIGH"
    assert payment["payment_signal"] == "PAYMENT_FAILED"


def test_payment_summary():
    payments = build_payment_intelligence(
        [
            {
                "payment_id": "pay-1",
                "amount": 100000,
                "status": "captured",
            },
            {
                "payment_id": "pay-2",
                "amount": 50000,
                "status": "failed",
            },
            {
                "payment_id": "pay-3",
                "amount": 25000,
                "status": "pending",
            },
        ]
    )

    summary = summarize_payment_behavior(payments)

    assert summary["total_payments"] == 3
    assert summary["successful_payments"] == 1
    assert summary["failed_payments"] == 1
    assert summary["pending_payments"] == 1
    assert summary["realized_amount"] == 100000.0
    assert summary["attempted_amount"] == 175000.0
    assert summary["read_only"] is True


def test_payment_intelligence_deterministic():
    payload = [
        {
            "payment_id": "det-pay",
            "customer_id": "customer-1",
            "amount": 75000,
            "status": "captured",
        }
    ]

    first = build_payment_intelligence(payload)
    second = build_payment_intelligence(payload)

    assert first == second


def test_api_contains_payment_intelligence():
    response = analyze_revenue(
        [
            {
                "invoice_id": "inv-api",
                "customer_id": "customer-47",
                "amount": 200000,
                "outstanding_amount": 100000,
                "days_overdue": 30,
            }
        ],
        [
            {
                "payment_id": "pay-api",
                "customer_id": "customer-47",
                "invoice_id": "inv-api",
                "amount": 50000,
                "status": "captured",
            }
        ],
        decision_id="phase3-api-test",
    )

    assert response.payments
    assert response.payments[0]["payment_id"] == "pay-api"

    assert response.payment_summary["total_payments"] == 1
    assert response.payment_summary["successful_payments"] == 1

    assert response.safety["execution_allowed"] is False
    assert response.safety["automatic_action"] is False
    assert response.safety["financial_mutation"] is False
    assert response.safety["provider_mutation"] is False
