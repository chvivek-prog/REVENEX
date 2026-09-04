from revenex.api.revenue_intelligence import (
    analyze_revenue,
    response_to_dict,
)
from revenex.persistence.outcome_store import OutcomeStore


def test_api_returns_revenue_intelligence():
    store = OutcomeStore()

    response = analyze_revenue(
        [
            {
                "customer_id": "customer-api",
                "amount": 200000,
                "outstanding_amount": 150000,
                "days_overdue": 90,
            }
        ],
        [],
        decision_id="api-44",
        store=store,
    )

    assert response.decision_id == "api-44"
    assert response.risk["total_outstanding"] == 150000
    assert "recommended_action" in response.decision
    assert "rationale" in response.audit
    assert response.outcome["status"] == "PENDING"

    store.close()


def test_api_exposes_complete_pipeline():
    response = analyze_revenue(
        [],
        [],
        decision_id="empty-api",
    )

    assert response.audit["stages"] == [
        "OBSERVE",
        "INVESTIGATE",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "EXPLAIN",
        "AUDIT",
    ]


def test_api_is_read_only():
    store = OutcomeStore()

    response = analyze_revenue(
        [
            {
                "customer_id": "safe-api",
                "amount": 100000,
                "outstanding_amount": 80000,
                "days_overdue": 90,
            }
        ],
        [],
        decision_id="safe-api",
        store=store,
    )

    assert response.safety == {
        "execution_allowed": False,
        "automatic_action": False,
        "financial_mutation": False,
        "provider_mutation": False,
    }

    store.close()


def test_api_response_is_serializable():
    response = analyze_revenue(
        [],
        [],
        decision_id="serialize-api",
    )

    data = response_to_dict(response)

    assert isinstance(data, dict)
    assert data["decision_id"] == "serialize-api"
    assert "risk" in data
    assert "decision" in data
    assert "audit" in data
    assert "outcome" in data
    assert "learning" in data
    assert "safety" in data


def test_api_persists_pending_outcome():
    store = OutcomeStore()

    analyze_revenue(
        [
            {
                "customer_id": "persistent-api",
                "amount": 100000,
                "outstanding_amount": 70000,
                "days_overdue": 60,
            }
        ],
        [],
        decision_id="persistent-api",
        store=store,
    )

    stored = store.get_outcome(
        "persistent-api"
    )

    assert stored is not None
    assert stored.status == "PENDING"

    store.close()
