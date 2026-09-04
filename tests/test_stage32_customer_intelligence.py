from revenex.customer.intelligence import (
    build_customer_profile,
    build_customer_profiles,
)


def test_customer_profile_calculates_revenue_metrics():
    profile = build_customer_profile(
        "customer-1",
        [
            {
                "customer_id": "customer-1",
                "amount": 100000,
                "outstanding_amount": 25000,
                "days_overdue": 10,
            }
        ],
        [
            {
                "customer_id": "customer-1",
                "amount": 75000,
            }
        ],
    )

    assert profile.invoice_count == 1
    assert profile.payment_count == 1
    assert profile.total_invoiced == 100000
    assert profile.total_paid == 75000
    assert profile.outstanding == 25000
    assert profile.collection_rate == 0.75


def test_customer_profile_detects_overdue_risk():
    profile = build_customer_profile(
        "customer-1",
        [
            {
                "customer_id": "customer-1",
                "amount": 200000,
                "outstanding_amount": 150000,
                "days_overdue": 90,
            }
        ],
        [],
    )

    assert profile.overdue_amount == 150000
    assert profile.overdue_invoice_count == 1
    assert profile.risk_score >= 0.70
    assert profile.health in {"AT_RISK", "CRITICAL"}


def test_profiles_are_created_for_all_customers():
    profiles = build_customer_profiles(
        [
            {
                "customer_id": "customer-a",
                "amount": 10000,
                "outstanding_amount": 0,
            },
            {
                "customer_id": "customer-b",
                "amount": 20000,
                "outstanding_amount": 10000,
            },
        ],
        [],
    )

    assert len(profiles) == 2
    assert {
        profile.customer_id
        for profile in profiles
    } == {"customer-a", "customer-b"}


def test_customer_intelligence_is_read_only():
    invoices = [
        {
            "customer_id": "customer-1",
            "amount": 100000,
            "outstanding_amount": 50000,
            "days_overdue": 60,
        }
    ]

    original = [dict(invoice) for invoice in invoices]

    build_customer_profile(
        "customer-1",
        invoices,
        [],
    )

    assert invoices == original
