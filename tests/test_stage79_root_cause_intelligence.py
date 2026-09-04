from revenex.root_cause_intelligence import (
    RootCauseCategory,
    analyze_root_causes,
    summarize_root_causes,
)


def test_unpaid_invoices_are_root_cause():
    causes = analyze_root_causes(
        expected_revenue=100000,
        actual_revenue=70000,
        unpaid_invoices=[
            {
                "invoice_id": "i1",
                "amount": 30000,
            }
        ],
    )

    assert len(causes) == 1
    assert causes[0].category == RootCauseCategory.COLLECTION
    assert causes[0].affected_amount == 30000.0
    assert causes[0].human_review_required is True
    assert causes[0].read_only is True
    assert causes[0].financial_mutation is False
    assert causes[0].provider_mutation is False


def test_multiple_root_causes_are_ranked():
    causes = analyze_root_causes(
        expected_revenue=200000,
        actual_revenue=100000,
        unpaid_invoices=[
            {"invoice_id": "i1", "amount": 50000},
        ],
        payment_failures=[
            {"payment_id": "p1", "amount": 30000},
        ],
        settlement_gaps=[
            {"settlement_id": "s1", "amount": 20000},
        ],
    )

    assert len(causes) == 3
    assert causes[0].affected_amount == 50000.0
    assert causes[0].contribution == 0.5


def test_unknown_root_cause_does_not_invent_evidence():
    causes = analyze_root_causes(
        expected_revenue=100000,
        actual_revenue=80000,
    )

    assert len(causes) == 1
    assert causes[0].category == RootCauseCategory.UNKNOWN
    assert causes[0].confidence < 0.5


def test_root_cause_summary_is_safe():
    causes = analyze_root_causes(
        expected_revenue=100000,
        actual_revenue=50000,
        unpaid_invoices=[
            {"invoice_id": "i1", "amount": 50000},
        ],
    )

    report = summarize_root_causes(causes)

    assert report.total_causes == 1
    assert report.primary_cause is not None
    assert report.affected_revenue == 50000.0
    assert report.human_review_required is True
    assert report.read_only is True
    assert report.financial_mutation is False
    assert report.provider_mutation is False
