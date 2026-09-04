
from revenex.api.revenue_intelligence import analyze_revenue
from revenex.payout.intelligence import (
    build_payout_intelligence,
    summarize_payout_behavior,
)
from revenex.treasury.intelligence import (
    build_treasury_intelligence,
)


def test_payout_intelligence():
    result = build_payout_intelligence(
        [
            {
                "payout_id": "payout-1",
                "amount": 50000,
                "status": "processed",
            },
            {
                "payout_id": "payout-2",
                "amount": 25000,
                "status": "pending",
            },
            {
                "payout_id": "payout-3",
                "amount": 10000,
                "status": "failed",
            },
        ]
    )

    assert len(result) == 3
    assert result[0]["payout_signal"] == "PAYOUT_COMPLETED"
    assert result[1]["payout_signal"] == "PAYOUT_PENDING"
    assert result[2]["payout_signal"] == "PAYOUT_EXCEPTION"
    assert result[1]["amount"] == 25000.0
    assert result[0]["read_only"] is True


def test_payout_summary():
    result = build_payout_intelligence(
        [
            {
                "payout_id": "payout-1",
                "amount": 50000,
                "status": "processed",
            },
            {
                "payout_id": "payout-2",
                "amount": 25000,
                "status": "pending",
            },
            {
                "payout_id": "payout-3",
                "amount": 10000,
                "status": "failed",
            },
        ]
    )

    summary = summarize_payout_behavior(result)

    assert summary["total_payouts"] == 3
    assert summary["completed_payouts"] == 1
    assert summary["pending_payouts"] == 1
    assert summary["exception_payouts"] == 1
    assert summary["payout_value"] == 85000.0
    assert summary["pending_payout_value"] == 25000.0
    assert summary["exception_payout_value"] == 10000.0


def test_treasury_intelligence():
    result = build_treasury_intelligence(
        captured_payment_value=500000,
        refund_value=20000,
        pending_settlement_value=50000,
        pending_payout_value=30000,
        receivables_exposure=100000,
    )

    assert result["captured_inflow"] == 500000.0
    assert result["refund_outflow"] == 20000.0
    assert result["available_inflow"] == 480000.0
    assert result["committed_outflow"] == 80000.0
    assert result["near_term_cash_position"] == 400000.0
    assert result["liquidity_exposure"] == 180000.0
    assert result["liquidity_signal"] == "LIQUIDITY_STABLE"
    assert result["read_only"] is True


def test_treasury_liquidity_pressure():
    result = build_treasury_intelligence(
        captured_payment_value=100000,
        refund_value=10000,
        pending_settlement_value=80000,
        pending_payout_value=30000,
        receivables_exposure=50000,
    )

    assert result["near_term_cash_position"] < 0
    assert result["liquidity_signal"] == "LIQUIDITY_PRESSURE"


def test_api_contains_phase7():
    response = analyze_revenue(
        [
            {
                "invoice_id": "inv-1",
                "customer_id": "customer-1",
                "amount": 100000,
                "outstanding_amount": 50000,
                "days_overdue": 30,
            }
        ],
        [
            {
                "payment_id": "pay-1",
                "customer_id": "customer-1",
                "amount": 90000,
                "status": "captured",
            },
            {
                "payout_id": "payout-1",
                "amount": 10000,
                "status": "pending",
                "type": "payout",
            },
        ],
        decision_id="phase7-api-test",
    )

    assert hasattr(response, "payouts")
    assert hasattr(response, "payout_summary")
    assert hasattr(response, "treasury")

    assert response.safety["execution_allowed"] is False
    assert response.safety["automatic_action"] is False
    assert response.safety["financial_mutation"] is False
    assert response.safety["provider_mutation"] is False
