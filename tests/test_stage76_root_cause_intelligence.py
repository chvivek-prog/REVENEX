from revenex.root_cause import (
    RootCauseCategory,
    analyze_root_causes,
    summarize_root_causes,
)


def test_settlement_root_cause():
    findings = analyze_root_causes(
        anomalies=[
            {
                "anomaly_type": "SETTLEMENT_VARIANCE",
                "entity_type": "settlement",
                "entity_id": "s1",
                "variance": -10000,
            }
        ],
        payments=[
            {
                "payment_id": "p1",
                "amount": 100000,
            }
        ],
        settlements=[
            {
                "settlement_id": "s1",
                "payment_id": "p1",
                "amount": 90000,
            }
        ],
    )

    assert len(findings) == 1
    assert (
        findings[0].category
        == RootCauseCategory.SETTLEMENT
    )
    assert findings[0].exposure == 10000.0
    assert findings[0].confidence >= 0.80


def test_refund_root_cause():
    findings = analyze_root_causes(
        anomalies=[
            {
                "anomaly_type": "REFUND_SPIKE",
                "entity_type": "refund",
                "entity_id": "r1",
                "exposure": 30000,
            }
        ],
        payments=[
            {
                "payment_id": "p1",
                "amount": 100000,
            }
        ],
        refunds=[
            {
                "refund_id": "r1",
                "payment_id": "p1",
                "amount": 30000,
            }
        ],
    )

    assert len(findings) == 1
    assert findings[0].category == RootCauseCategory.REFUND
    assert "refund_activity" in findings[0].contributing_factors


def test_unknown_root_cause_is_explicit():
    findings = analyze_root_causes(
        anomalies=[
            {
                "anomaly_type": "UNKNOWN_EVENT",
                "entity_type": "event",
                "entity_id": "e1",
                "exposure": 5000,
            }
        ]
    )

    assert len(findings) == 1
    assert findings[0].category == RootCauseCategory.UNKNOWN
    assert findings[0].confidence == 0.5


def test_root_cause_summary_is_safe():
    findings = analyze_root_causes(
        anomalies=[
            {
                "anomaly_type": "PAYMENT_SPIKE",
                "entity_type": "payment",
                "entity_id": "p1",
                "exposure": 50000,
            }
        ],
        payments=[
            {
                "payment_id": "p1",
                "amount": 50000,
            }
        ],
    )

    report = summarize_root_causes(findings)

    assert report.total_findings == 1
    assert report.total_exposure == 50000.0
    assert report.high_confidence_count == 1
    assert report.human_review_required is True
    assert report.read_only is True
    assert report.financial_mutation is False
    assert report.provider_mutation is False
