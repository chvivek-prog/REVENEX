from revenex.customer.customer_360 import (
    build_customer_360,
    build_customer_360_views,
)


def test_customer_360_combines_financial_signals():
    view = build_customer_360(
        "customer-1",
        [
            {
                "customer_id": "customer-1",
                "amount": 100000,
                "outstanding_amount": 60000,
                "days_overdue": 60,
            },
            {
                "customer_id": "customer-2",
                "amount": 300000,
                "outstanding_amount": 0,
            },
        ],
        [
            {
                "customer_id": "customer-1",
                "amount": 40000,
            }
        ],
    )

    assert view.customer_id == "customer-1"
    assert view.financial.total_invoiced == 100000
    assert view.financial.outstanding == 60000
    assert view.revenue_share == 0.25
    assert view.average_invoice_value == 100000
    assert view.average_payment_value == 40000


def test_customer_360_identifies_recovery_focus():
    view = build_customer_360(
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

    assert view.attention_level in {"HIGH", "CRITICAL"}
    assert view.recommended_focus == "RECOVERY"
    assert view.overdue_ratio == 1.0
    assert view.outstanding_ratio == 0.75


def test_customer_360_builds_multiple_customers():
    views = build_customer_360_views(
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

    assert len(views) == 2
    assert [view.customer_id for view in views] == [
        "customer-a",
        "customer-b",
    ]


def test_customer_360_is_read_only():
    invoices = [
        {
            "customer_id": "customer-1",
            "amount": 100000,
            "outstanding_amount": 50000,
            "days_overdue": 45,
        }
    ]

    payments = [
        {
            "customer_id": "customer-1",
            "amount": 50000,
        }
    ]

    invoices_before = [dict(item) for item in invoices]
    payments_before = [dict(item) for item in payments]

    build_customer_360(
        "customer-1",
        invoices,
        payments,
    )

    assert invoices == invoices_before
    assert payments == payments_before
