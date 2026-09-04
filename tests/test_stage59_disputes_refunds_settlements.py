
from revenex.disputes.intelligence import (
    build_dispute_intelligence,
    summarize_dispute_behavior,
)
from revenex.refunds.intelligence import (
    build_refund_intelligence,
    summarize_refund_behavior,
)
from revenex.settlements.exceptions import (
    analyze_settlement_exceptions,
    summarize_settlement_exceptions,
)
from revenex.exceptions.governance import (
    build_exception_governance,
)


def test_dispute_intelligence():
    result = build_dispute_intelligence(
        [
            {
                "dispute_id": "d1",
                "amount": 10000,
                "status": "open",
                "reason": "fraud",
            },
            {
                "dispute_id": "d2",
                "amount": 5000,
                "status": "won",
            },
            {
                "dispute_id": "d3",
                "amount": 2000,
                "status": "lost",
            },
        ]
    )

    assert len(result) == 3
    assert result[0]["dispute_signal"] == (
        "DISPUTE_REVIEW_REQUIRED"
    )
    assert result[0]["risk_level"] == "HIGH"
    assert result[1]["dispute_signal"] == (
        "DISPUTE_RESOLVED"
    )
    assert result[2]["dispute_signal"] == (
        "DISPUTE_LOSS"
    )


def test_dispute_summary():
    result = build_dispute_intelligence(
        [
            {
                "dispute_id": "d1",
                "amount": 10000,
                "status": "open",
            },
            {
                "dispute_id": "d2",
                "amount": 5000,
                "status": "lost",
            },
        ]
    )

    summary = summarize_dispute_behavior(result)

    assert summary["total_disputes"] == 2
    assert summary["open_disputes"] == 1
    assert summary["lost_disputes"] == 1
    assert summary["total_dispute_exposure"] == 15000.0
    assert summary["open_dispute_exposure"] == 10000.0
    assert summary["lost_dispute_exposure"] == 5000.0
    assert summary["human_review_required"] is True


def test_refund_intelligence():
    result = build_refund_intelligence(
        [
            {
                "refund_id": "r1",
                "amount": 1000,
                "status": "completed",
            },
            {
                "refund_id": "r2",
                "amount": 2000,
                "status": "pending",
            },
            {
                "refund_id": "r3",
                "amount": 3000,
                "status": "failed",
            },
        ]
    )

    assert result[0]["refund_signal"] == (
        "REFUND_COMPLETED"
    )
    assert result[1]["refund_signal"] == (
        "REFUND_PENDING"
    )
    assert result[2]["refund_signal"] == (
        "REFUND_EXCEPTION"
    )


def test_refund_summary():
    result = build_refund_intelligence(
        [
            {
                "refund_id": "r1",
                "amount": 1000,
                "status": "completed",
            },
            {
                "refund_id": "r2",
                "amount": 2000,
                "status": "pending",
            },
            {
                "refund_id": "r3",
                "amount": 3000,
                "status": "failed",
            },
        ]
    )

    summary = summarize_refund_behavior(result)

    assert summary["total_refunds"] == 3
    assert summary["completed_refunds"] == 1
    assert summary["pending_refunds"] == 1
    assert summary["exception_refunds"] == 1
    assert summary["refund_value"] == 6000.0
    assert summary["pending_refund_value"] == 2000.0
    assert summary["exception_refund_value"] == 3000.0


def test_settlement_reconciled():
    result = analyze_settlement_exceptions(
        [
            {
                "settlement_id": "s1",
                "expected_amount": 100000,
                "observed_amount": 100000,
                "status": "completed",
            }
        ]
    )

    assert result[0]["settlement_signal"] == (
        "SETTLEMENT_RECONCILED"
    )
    assert result[0]["exception"] is False


def test_settlement_variance():
    result = analyze_settlement_exceptions(
        [
            {
                "settlement_id": "s1",
                "expected_amount": 100000,
                "observed_amount": 97000,
                "status": "completed",
            }
        ]
    )

    assert result[0]["settlement_signal"] == (
        "SETTLEMENT_AMOUNT_VARIANCE"
    )
    assert result[0]["variance"] == -3000.0
    assert result[0]["exception"] is True
    assert result[0]["severity"] == "HIGH"


def test_settlement_summary():
    result = analyze_settlement_exceptions(
        [
            {
                "settlement_id": "s1",
                "expected_amount": 100000,
                "observed_amount": 100000,
                "status": "completed",
            },
            {
                "settlement_id": "s2",
                "expected_amount": 50000,
                "observed_amount": 45000,
                "status": "completed",
            },
        ]
    )

    summary = summarize_settlement_exceptions(result)

    assert summary["total_settlements"] == 2
    assert summary["reconciled_count"] == 1
    assert summary["exception_count"] == 1
    assert summary["variance_count"] == 1
    assert summary["exception_exposure"] == 5000.0
    assert summary["human_review_required"] is True


def test_exception_governance():
    result = build_exception_governance(
        disputes={
            "open_disputes": 2,
        },
        refunds={
            "exception_refunds": 1,
        },
        settlements={
            "exception_count": 2,
        },
    )

    assert result["exception_count"] == 5
    assert result["priority"] == "HIGH"
    assert result["recommended_action"] == (
        "EXECUTIVE_REVIEW"
    )
    assert result["human_approval_required"] is True
    assert result["automatic_action"] is False
    assert result["financial_mutation"] is False
    assert result["provider_mutation"] is False
    assert result["read_only"] is True
