
from revenex.control_tower import (
    build_control_tower,
    build_executive_summary,
)


def test_control_tower_unifies_revenue_state():

    result = build_control_tower(
        revenue={
            "total_outstanding": 550000,
            "total_revenue_at_risk": 428500,
            "expected_collection": 483120,
        },
        invoices={
            "total_invoices": 10,
            "total_outstanding": 550000,
        },
        payments={
            "total_payments": 8,
            "failed_payments": 1,
        },
        orders={
            "total_orders": 20,
        },
        subscriptions={
            "active_subscriptions": 4,
        },
        disputes={
            "open_disputes": 2,
            "open_dispute_exposure": 50000,
        },
        refunds={
            "exception_refunds": 1,
            "exception_refund_value": 10000,
        },
        settlements={
            "exception_count": 1,
            "exception_exposure": 5000,
        },
        webhooks={
            "failed_count": 2,
        },
        payouts={
            "exception_count": 1,
        },
        reconciliation={
            "exception_count": 1,
        },
        learning={
            "learning_signal": "WAIT_FOR_OUTCOME",
            "evaluation_status": "INSUFFICIENT_DATA",
        },
    )

    assert result["revenue"]["outstanding"] == 550000.0
    assert result["revenue"]["revenue_at_risk"] == 428500.0
    assert result["revenue"]["expected_collection"] == 483120.0

    assert result["operations"]["exception_count"] == 5
    assert result["operations"]["operational_alerts"] == 4

    assert result["executive_state"] == "CRITICAL"
    assert result["priority"] == "HIGH"


def test_control_tower_pipeline():

    result = build_control_tower()

    assert result["pipeline"] == [
        "OBSERVE",
        "INVESTIGATE",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "MONITOR",
        "LEARN",
        "AUDIT",
    ]


def test_control_tower_safety_boundary():

    result = build_control_tower()

    safety = result["safety"]

    assert safety["execution_allowed"] is False
    assert safety["automatic_action"] is False
    assert safety["financial_mutation"] is False
    assert safety["provider_mutation"] is False
    assert safety["human_approval_required"] is True
    assert result["read_only"] is True


def test_control_tower_learning_is_advisory():

    result = build_control_tower(
        learning={
            "learning_signal": "UNDERPREDICTED_COLLECTION",
            "learning_confidence": 0.82,
            "evaluation_status": "EVALUATED",
        }
    )

    assert (
        result["learning"]["signal"]
        == "UNDERPREDICTED_COLLECTION"
    )

    assert (
        result["learning"]["confidence"]
        == 0.82
    )

    assert (
        result["learning"]
        ["automatic_model_mutation"]
        is False
    )


def test_executive_summary():

    result = build_control_tower(
        revenue={
            "total_outstanding": 100000,
            "total_revenue_at_risk": 25000,
            "expected_collection": 80000,
        }
    )

    summary = build_executive_summary(result)

    assert "REVENEX state=" in summary
    assert "Outstanding revenue=" in summary
    assert "Revenue at risk=" in summary
    assert "Human approval remains required." in summary
