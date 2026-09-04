from revenex.phase16 import (
    CorrelationSeverity,
    correlate_revenue_systems,
)


def test_collection_gap_is_detected():
    report = correlate_revenue_systems(
        [
            {
                "entity_id": "customer-47",
                "invoice_amount": 100000,
                "payment_amount": 70000,
                "settlement_amount": 70000,
                "payout_amount": 70000,
            }
        ]
    )

    assert len(report.signals) == 1

    signal = report.signals[0]

    assert signal.collection_gap == 30000
    assert signal.settlement_gap == 0
    assert signal.payout_gap == 0
    assert signal.signal == "CROSS_SYSTEM_COLLECTION_GAP"


def test_settlement_gap_is_detected():
    report = correlate_revenue_systems(
        [
            {
                "entity_id": "customer-1",
                "invoice_amount": 100000,
                "payment_amount": 100000,
                "settlement_amount": 90000,
                "payout_amount": 90000,
            }
        ]
    )

    signal = report.signals[0]

    assert signal.collection_gap == 0
    assert signal.settlement_gap == 10000
    assert signal.signal == "CROSS_SYSTEM_SETTLEMENT_GAP"


def test_payout_gap_is_detected():
    report = correlate_revenue_systems(
        [
            {
                "entity_id": "customer-2",
                "invoice_amount": 100000,
                "payment_amount": 100000,
                "settlement_amount": 100000,
                "payout_amount": 80000,
            }
        ]
    )

    signal = report.signals[0]

    assert signal.collection_gap == 0
    assert signal.settlement_gap == 0
    assert signal.payout_gap == 20000
    assert signal.signal == "CROSS_SYSTEM_PAYOUT_GAP"


def test_multiple_gaps_are_correlated():
    report = correlate_revenue_systems(
        [
            {
                "entity_id": "customer-3",
                "invoice_amount": 100000,
                "payment_amount": 80000,
                "settlement_amount": 70000,
                "payout_amount": 60000,
            }
        ]
    )

    signal = report.signals[0]

    assert signal.collection_gap == 20000
    assert signal.settlement_gap == 10000
    assert signal.payout_gap == 10000
    assert signal.correlation_score == 0.4
    assert signal.severity == CorrelationSeverity.HIGH


def test_aligned_record_produces_no_signal():
    report = correlate_revenue_systems(
        [
            {
                "entity_id": "customer-aligned",
                "invoice_amount": 100000,
                "payment_amount": 100000,
                "settlement_amount": 100000,
                "payout_amount": 100000,
            }
        ]
    )

    assert report.signals == ()
    assert report.correlated_entities == 0
    assert report.total_collection_gap == 0
    assert report.total_settlement_gap == 0
    assert report.total_payout_gap == 0


def test_report_aggregates_gaps():
    report = correlate_revenue_systems(
        [
            {
                "entity_id": "a",
                "invoice_amount": 100000,
                "payment_amount": 90000,
                "settlement_amount": 80000,
                "payout_amount": 70000,
            },
            {
                "entity_id": "b",
                "invoice_amount": 200000,
                "payment_amount": 150000,
                "settlement_amount": 140000,
                "payout_amount": 130000,
            },
        ]
    )

    assert report.entities_analyzed == 2
    assert report.correlated_entities == 2
    assert report.total_collection_gap == 60000
    assert report.total_settlement_gap == 20000
    assert report.total_payout_gap == 20000


def test_signals_are_ranked_by_correlation_score():
    report = correlate_revenue_systems(
        [
            {
                "entity_id": "low",
                "invoice_amount": 100000,
                "payment_amount": 95000,
                "settlement_amount": 95000,
                "payout_amount": 95000,
            },
            {
                "entity_id": "high",
                "invoice_amount": 100000,
                "payment_amount": 50000,
                "settlement_amount": 40000,
                "payout_amount": 30000,
            },
        ]
    )

    assert report.signals[0].entity_id == "high"


def test_governance_is_locked():
    report = correlate_revenue_systems(
        [
            {
                "entity_id": "customer-1",
                "invoice_amount": 100000,
                "payment_amount": 50000,
                "settlement_amount": 40000,
                "payout_amount": 30000,
            }
        ]
    )

    assert report.read_only is True
    assert report.human_review_required is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False

    signal = report.signals[0]

    assert signal.read_only is True
    assert signal.human_review_required is True


def test_correlation_is_deterministic():
    records = [
        {
            "entity_id": "a",
            "invoice_amount": 100000,
            "payment_amount": 80000,
            "settlement_amount": 70000,
            "payout_amount": 60000,
        },
        {
            "entity_id": "b",
            "invoice_amount": 200000,
            "payment_amount": 180000,
            "settlement_amount": 180000,
            "payout_amount": 170000,
        },
    ]

    first = correlate_revenue_systems(records)
    second = correlate_revenue_systems(records)

    assert first == second
