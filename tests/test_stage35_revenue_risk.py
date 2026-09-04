from revenex.risk.revenue_risk import (
    build_revenue_risk_report,
    rank_customer_risks,
)


def test_revenue_risk_aggregates_customer_exposure():
    report = build_revenue_risk_report(
        [
            {
                "customer_id": "customer-a",
                "amount": 200000,
                "outstanding_amount": 180000,
                "days_overdue": 90,
            },
            {
                "customer_id": "customer-b",
                "amount": 100000,
                "outstanding_amount": 10000,
                "days_overdue": 10,
            },
        ],
        [],
    )

    assert report.total_outstanding == 190000
    assert report.total_revenue_at_risk > 0
    assert report.expected_collection >= 0
    assert len(report.customer_risks) == 2


def test_revenue_risk_identifies_critical_exposure():
    report = build_revenue_risk_report(
        [
            {
                "customer_id": "customer-a",
                "amount": 1000000,
                "outstanding_amount": 950000,
                "days_overdue": 180,
            }
        ],
        [],
    )

    assert report.critical_customer_count == 1
    assert report.critical_risk_exposure > 0
    assert report.high_risk_exposure > 0


def test_customer_risks_are_ranked_by_exposure():
    report = build_revenue_risk_report(
        [
            {
                "customer_id": "customer-a",
                "amount": 100000,
                "outstanding_amount": 90000,
                "days_overdue": 120,
            },
            {
                "customer_id": "customer-b",
                "amount": 500000,
                "outstanding_amount": 200000,
                "days_overdue": 90,
            },
        ],
        [],
    )

    ranked = rank_customer_risks(report)

    assert len(ranked) == 2
    assert ranked[0].revenue_at_risk >= ranked[1].revenue_at_risk


def test_risk_concentration_is_bounded():
    report = build_revenue_risk_report(
        [
            {
                "customer_id": "customer-a",
                "amount": 100000,
                "outstanding_amount": 90000,
                "days_overdue": 120,
            }
        ],
        [],
    )

    assert 0.0 <= report.concentration_ratio <= 1.0


def test_empty_portfolio_is_safe():
    report = build_revenue_risk_report([], [])

    assert report.total_outstanding == 0
    assert report.total_revenue_at_risk == 0
    assert report.expected_collection == 0
    assert report.high_risk_customer_count == 0
    assert report.critical_customer_count == 0
    assert report.customer_risks == ()


def test_risk_layer_is_read_only():
    invoices = [
        {
            "customer_id": "customer-a",
            "amount": 100000,
            "outstanding_amount": 80000,
            "days_overdue": 60,
        }
    ]

    payments = [
        {
            "customer_id": "customer-a",
            "amount": 20000,
        }
    ]

    invoices_before = [dict(item) for item in invoices]
    payments_before = [dict(item) for item in payments]

    build_revenue_risk_report(
        invoices,
        payments,
    )

    assert invoices == invoices_before
    assert payments == payments_before
