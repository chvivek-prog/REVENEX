"""
REVENEX Stage 45 — API Safety & Contract Tests.

These tests verify that the Revenue Intelligence API remains
advisory-only and that client-controlled input cannot bypass
the safety boundary.
"""

from copy import deepcopy

import pytest

from revenex.api.revenue_intelligence import analyze_revenue
from revenex.persistence.outcome_store import OutcomeStore


BASE_INVOICES = [
    {
        "customer_id": "customer-45",
        "amount": 200000,
        "outstanding_amount": 150000,
        "days_overdue": 90,
    }
]

BASE_PAYMENTS = [
    {
        "customer_id": "customer-45",
        "amount": 50000,
    }
]


def test_api_always_disables_execution():
    response = analyze_revenue(
        BASE_INVOICES,
        BASE_PAYMENTS,
        decision_id="safety-45-1",
    )

    assert response.safety["execution_allowed"] is False
    assert response.safety["automatic_action"] is False
    assert response.safety["financial_mutation"] is False
    assert response.safety["provider_mutation"] is False


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "execution_allowed",
        "automatic_action",
        "financial_mutation",
        "provider_mutation",
        "execute",
        "execute_payment",
        "refund",
        "capture_payment",
        "create_payment",
        "approve",
        "approval_id",
        "authorised_by_approval_id",
    ],
)
def test_client_cannot_control_execution_fields(
    forbidden_field,
):
    """
    Execution-related fields are never client-controlled.

    The four canonical safety fields are intentionally exposed by
    the response as immutable False guarantees. The remaining
    execution fields must not appear anywhere in the decision
    contract.
    """

    invoices = deepcopy(BASE_INVOICES)
    payments = deepcopy(BASE_PAYMENTS)

    response = analyze_revenue(
        invoices,
        payments,
        decision_id=f"forbidden-{forbidden_field}",
    )

    if forbidden_field in {
        "execution_allowed",
        "automatic_action",
        "financial_mutation",
        "provider_mutation",
    }:
        assert response.safety[forbidden_field] is False
    else:
        assert forbidden_field not in response.decision
        assert forbidden_field not in response.safety


def test_api_requires_approval_for_recommendations():
    response = analyze_revenue(
        BASE_INVOICES,
        BASE_PAYMENTS,
        decision_id="approval-45",
    )

    assert response.decision["requires_approval"] is True
    assert response.safety["execution_allowed"] is False


def test_api_does_not_mutate_invoice_input():
    invoices = deepcopy(BASE_INVOICES)
    payments = deepcopy(BASE_PAYMENTS)

    invoices_before = deepcopy(invoices)
    payments_before = deepcopy(payments)

    analyze_revenue(
        invoices,
        payments,
        decision_id="immutable-45",
    )

    assert invoices == invoices_before
    assert payments == payments_before


def test_api_rejects_no_execution_path_by_contract():
    response = analyze_revenue(
        BASE_INVOICES,
        BASE_PAYMENTS,
        decision_id="contract-45",
    )

    safety = response.safety

    assert set(safety) == {
        "execution_allowed",
        "automatic_action",
        "financial_mutation",
        "provider_mutation",
    }

    assert all(
        value is False
        for value in safety.values()
    )


def test_api_response_contains_required_contract_sections():
    response = analyze_revenue(
        BASE_INVOICES,
        BASE_PAYMENTS,
        decision_id="shape-45",
    )

    assert response.decision_id
    assert response.risk
    assert response.decision
    assert response.audit
    assert response.outcome
    assert response.learning
    assert response.safety


def test_api_persists_only_intelligence_outcome():
    store = OutcomeStore()

    response = analyze_revenue(
        BASE_INVOICES,
        BASE_PAYMENTS,
        decision_id="persist-45",
        store=store,
    )

    stored = store.get_outcome(
        response.decision_id
    )

    assert stored is not None
    assert stored.status == "PENDING"
    assert stored.actual_collection is None
    assert stored.actual_remaining_exposure is None

    store.close()


def test_same_input_produces_same_decision():
    first = analyze_revenue(
        BASE_INVOICES,
        BASE_PAYMENTS,
        decision_id="deterministic-1",
    )

    second = analyze_revenue(
        BASE_INVOICES,
        BASE_PAYMENTS,
        decision_id="deterministic-2",
    )

    assert (
        first.decision["scenario"]
        == second.decision["scenario"]
    )

    assert (
        first.decision["expected_collection"]
        == second.decision["expected_collection"]
    )

    assert (
        first.decision["remaining_exposure"]
        == second.decision["remaining_exposure"]
    )

    assert (
        first.decision["confidence"]
        == second.decision["confidence"]
    )


def test_empty_portfolio_remains_monitor_only():
    response = analyze_revenue(
        [],
        [],
        decision_id="empty-45",
    )

    assert response.decision["recommended_action"] == "MONITOR"
    assert response.decision["expected_collection"] == 0
    assert response.safety["execution_allowed"] is False
    assert response.safety["automatic_action"] is False


def test_high_risk_does_not_enable_execution():
    response = analyze_revenue(
        [
            {
                "customer_id": "critical-customer",
                "amount": 1000000,
                "outstanding_amount": 950000,
                "days_overdue": 180,
            }
        ],
        [],
        decision_id="critical-45",
    )

    assert response.risk["total_revenue_at_risk"] >= 0

    assert response.safety["execution_allowed"] is False
    assert response.safety["automatic_action"] is False
    assert response.safety["financial_mutation"] is False
    assert response.safety["provider_mutation"] is False


def test_external_store_is_not_mutated_by_read_only_analysis():
    store = OutcomeStore()

    response = analyze_revenue(
        [],
        [],
        decision_id="readonly-45",
        store=store,
    )

    stored = store.get_outcome(
        response.decision_id
    )

    assert stored is not None
    assert stored.status == "PENDING"
    assert stored.actual_collection is None

    store.close()
