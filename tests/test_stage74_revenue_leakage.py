from revenex.leakage import (
    LeakageType,
    detect_revenue_leakage,
    summarize_revenue_leakage,
)


def test_unpaid_invoice_is_detected():
    leakages = detect_revenue_leakage(
        invoices=[
            {
                "invoice_id": "inv1",
                "amount": 100000,
                "outstanding_amount": 100000,
            }
        ],
        payments=[],
    )

    assert len(leakages) == 1
    assert (
        leakages[0].leakage_type
        == LeakageType.UNPAID_INVOICE
    )
    assert leakages[0].leakage_amount == 100000.0
    assert leakages[0].human_review_required is True
    assert leakages[0].read_only is True
    assert leakages[0].financial_mutation is False
    assert leakages[0].provider_mutation is False


def test_partial_payment_is_detected():
    leakages = detect_revenue_leakage(
        invoices=[
            {
                "invoice_id": "inv1",
                "amount": 100000,
                "outstanding_amount": 30000,
            }
        ],
        payments=[
            {
                "payment_id": "pay1",
                "invoice_id": "inv1",
                "amount": 70000,
            }
        ],
    )

    assert len(leakages) == 1
    assert (
        leakages[0].leakage_type
        == LeakageType.PARTIAL_PAYMENT
    )
    assert leakages[0].leakage_amount == 30000.0


def test_orphan_payment_is_detected():
    leakages = detect_revenue_leakage(
        payments=[
            {
                "payment_id": "pay-orphan",
                "amount": 50000,
            }
        ]
    )

    assert len(leakages) == 1
    assert (
        leakages[0].leakage_type
        == LeakageType.ORPHAN_PAYMENT
    )


def test_refund_and_dispute_exposure():
    leakages = detect_revenue_leakage(
        refunds=[
            {
                "refund_id": "refund1",
                "amount": 10000,
            }
        ],
        disputes=[
            {
                "dispute_id": "dispute1",
                "amount": 25000,
            }
        ],
    )

    assert len(leakages) == 2

    types = {
        item.leakage_type
        for item in leakages
    }

    assert LeakageType.REFUND_EXPOSURE in types
    assert LeakageType.DISPUTE_EXPOSURE in types


def test_settlement_gap_is_detected():
    leakages = detect_revenue_leakage(
        payments=[
            {
                "payment_id": "pay1",
                "amount": 100000,
            }
        ],
        settlements=[
            {
                "settlement_id": "set1",
                "payment_id": "pay1",
                "amount": 90000,
            }
        ],
    )

    assert len(leakages) == 1
    assert (
        leakages[0].leakage_type
        == LeakageType.SETTLEMENT_GAP
    )
    assert leakages[0].leakage_amount == 10000.0


def test_summary_aggregates_exposure():
    leakages = detect_revenue_leakage(
        invoices=[
            {
                "invoice_id": "inv1",
                "amount": 100000,
                "outstanding_amount": 100000,
            },
            {
                "invoice_id": "inv2",
                "amount": 50000,
                "outstanding_amount": 10000,
            },
        ],
        payments=[
            {
                "payment_id": "pay2",
                "invoice_id": "inv2",
                "amount": 40000,
            }
        ],
    )

    report = summarize_revenue_leakage(
        leakages
    )

    assert report.leakage_count == 2
    assert (
        report.unpaid_invoice_exposure
        == 100000.0
    )
    assert (
        report.partial_payment_exposure
        == 10000.0
    )
    assert (
        report.total_leakage_amount
        == 110000.0
    )
    assert report.human_review_required is True
    assert report.read_only is True
    assert report.financial_mutation is False
    assert report.provider_mutation is False


def test_no_leakage_is_clean():
    leakages = detect_revenue_leakage(
        invoices=[
            {
                "invoice_id": "inv1",
                "amount": 100000,
                "outstanding_amount": 0,
            }
        ],
        payments=[
            {
                "payment_id": "pay1",
                "invoice_id": "inv1",
                "amount": 100000,
            }
        ],
    )

    report = summarize_revenue_leakage(
        leakages
    )

    assert report.leakage_count == 0
    assert report.total_leakage_amount == 0.0
    assert "No revenue leakage" in (
        report.executive_summary
    )
