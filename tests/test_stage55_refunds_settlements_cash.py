
from revenex.api.revenue_intelligence import analyze_revenue
from revenex.refund.intelligence import (
    build_refund_intelligence,
    summarize_refund_behavior,
)
from revenex.settlement.intelligence import (
    build_settlement_intelligence,
    summarize_settlement_behavior,
)
from revenex.cash.intelligence import build_cash_intelligence


def test_refund_intelligence():
    result = build_refund_intelligence(
        [
            {
                "refund_id": "refund-1",
                "customer_id": "customer-1",
                "amount": 10000,
                "status": "processed",
            },
            {
                "refund_id": "refund-2",
                "customer_id": "customer-2",
                "amount": 5000,
                "status": "pending",
            },
        ]
    )

    assert len(result) == 2
    assert result[0]["refund_signal"] == "REFUND_COMPLETED"
    assert result[1]["refund_signal"] == "REFUND_PENDING"
    assert result[1]["amount"] == 5000.0
    assert result[0]["read_only"] is True


def test_refund_summary():
    result = build_refund_intelligence(
        [
            {
                "refund_id": "refund-1",
                "amount": 10000,
                "status": "processed",
            },
            {
                "refund_id": "refund-2",
                "amount": 5000,
                "status": "pending",
            },
            {
                "refund_id": "refund-3",
                "amount": 2000,
                "status": "failed",
            },
        ]
    )

    summary = summarize_refund_behavior(result)

    assert summary["total_refunds"] == 3
    assert summary["completed_refunds"] == 1
    assert summary["pending_refunds"] == 1
    assert summary["failed_refunds"] == 1
    assert summary["refund_value"] == 17000.0
    assert summary["pending_refund_exposure"] == 5000.0


def test_settlement_intelligence():
    result = build_settlement_intelligence(
        [
            {
                "settlement_id": "set-1",
                "amount": 100000,
                "expected_amount": 100000,
                "status": "processed",
            },
            {
                "settlement_id": "set-2",
                "amount": 50000,
                "expected_amount": 60000,
                "status": "pending",
            },
        ]
    )

    assert len(result) == 2
    assert result[0]["settlement_signal"] == "SETTLEMENT_RECEIVED"
    assert result[1]["settlement_signal"] == "SETTLEMENT_VARIANCE_REVIEW"
    assert result[1]["variance"] == -10000.0


def test_settlement_summary():
    result = build_settlement_intelligence(
        [
            {
                "settlement_id": "set-1",
                "amount": 100000,
                "expected_amount": 100000,
                "status": "processed",
            },
            {
                "settlement_id": "set-2",
                "amount": 50000,
                "expected_amount": 60000,
                "status": "pending",
            },
        ]
    )

    summary = summarize_settlement_behavior(result)

    assert summary["total_settlements"] == 2
    assert summary["received_settlements"] == 1
    assert summary["settlement_value"] == 150000.0
    assert summary["net_settlement_variance"] == -10000.0


def test_cash_intelligence():
    cash = build_cash_intelligence(
        payments=[
            {
                "amount": 100000,
                "status": "captured",
            },
            {
                "amount": 50000,
                "status": "failed",
            },
        ],
        refunds=[
            {
                "amount": 10000,
                "status": "processed",
            }
        ],
        settlements=[
            {
                "amount": 70000,
                "status": "processed",
            },
            {
                "amount": 30000,
                "status": "pending",
            },
        ],
    )

    assert cash["captured_payment_value"] == 100000.0
    assert cash["refund_value"] == 10000.0
    assert cash["net_payment_value"] == 90000.0
    assert cash["settlement_value"] == 100000.0
    assert cash["pending_settlement_value"] == 30000.0
    assert cash["cash_at_risk"] == 40000.0
    assert cash["read_only"] is True


def test_api_contains_phase5_intelligence():
    response = analyze_revenue(
        [
            {
                "invoice_id": "inv-1",
                "customer_id": "customer-1",
                "amount": 100000,
                "outstanding_amount": 50000,
                "days_overdue": 30,
                "refund_id": "refund-1",
                "refund_amount": 5000,
                "type": "refund",
                "settlement_id": "set-1",
            }
        ],
        [
            {
                "payment_id": "pay-1",
                "customer_id": "customer-1",
                "invoice_id": "inv-1",
                "amount": 95000,
                "status": "captured",
            }
        ],
        decision_id="phase5-api-test",
    )

    assert hasattr(response, "refunds")
    assert hasattr(response, "refund_summary")
    assert hasattr(response, "settlements")
    assert hasattr(response, "settlement_summary")
    assert hasattr(response, "cash")

    assert response.safety["execution_allowed"] is False
    assert response.safety["automatic_action"] is False
    assert response.safety["financial_mutation"] is False
    assert response.safety["provider_mutation"] is False
