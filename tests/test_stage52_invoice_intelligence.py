
from revenex.api.revenue_intelligence import analyze_revenue
from revenex.invoice.intelligence import build_invoice_intelligence


def test_invoice_intelligence_basic():
    result = build_invoice_intelligence(
        [
            {
                "invoice_id": "inv-1",
                "customer_id": "customer-47",
                "amount": 200000,
                "outstanding_amount": 150000,
                "days_overdue": 90,
            }
        ]
    )

    assert len(result) == 1

    invoice = result[0]

    assert invoice["invoice_id"] == "inv-1"
    assert invoice["customer_id"] == "customer-47"
    assert invoice["amount"] == 200000.0
    assert invoice["outstanding_amount"] == 150000.0
    assert invoice["days_overdue"] == 90
    assert invoice["risk_level"] in {
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }
    assert 0 <= invoice["collection_probability"] <= 1
    assert invoice["expected_collection"] >= 0
    assert invoice["remaining_exposure"] >= 0
    assert invoice["read_only"] is True


def test_invoice_paid_has_zero_exposure():
    result = build_invoice_intelligence(
        [
            {
                "invoice_id": "paid-1",
                "customer_id": "customer-1",
                "amount": 100000,
                "amount_paid": 100000,
                "status": "paid",
            }
        ]
    )

    invoice = result[0]

    assert invoice["amount_due"] == 0
    assert invoice["remaining_exposure"] == 0
    assert invoice["recommended_action"] == "MONITOR"


def test_invoice_intelligence_is_deterministic():
    payload = [
        {
            "invoice_id": "det-1",
            "customer_id": "customer-1",
            "amount": 500000,
            "outstanding_amount": 400000,
            "days_overdue": 120,
        }
    ]

    first = build_invoice_intelligence(payload)
    second = build_invoice_intelligence(payload)

    assert first == second


def test_api_contains_invoice_intelligence():
    response = analyze_revenue(
        [
            {
                "invoice_id": "api-inv-1",
                "customer_id": "customer-47",
                "amount": 200000,
                "outstanding_amount": 150000,
                "days_overdue": 90,
            }
        ],
        [],
        decision_id="phase2-api-test",
    )

    assert response.invoices
    assert response.invoices[0]["invoice_id"] == "api-inv-1"
    assert response.invoices[0]["read_only"] is True
    assert response.safety["execution_allowed"] is False
    assert response.safety["automatic_action"] is False
    assert response.safety["financial_mutation"] is False
    assert response.safety["provider_mutation"] is False
