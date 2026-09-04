from revenex.anomaly import (
    AnomalySeverity,
    AnomalyType,
    detect_revenue_anomalies,
    summarize_revenue_anomalies,
)


def test_payment_spike_is_detected():
    result = detect_revenue_anomalies(
        payments=[
            {
                "payment_id": "p1",
                "amount": 250000,
            }
        ],
        baselines={
            "payment_amount": 100000,
        },
    )

    assert len(result) == 1
    assert result[0].anomaly_type == AnomalyType.PAYMENT_SPIKE
    assert result[0].severity == AnomalySeverity.HIGH


def test_payment_drop_is_detected():
    result = detect_revenue_anomalies(
        payments=[
            {
                "payment_id": "p1",
                "amount": 40000,
            }
        ],
        baselines={
            "payment_amount": 100000,
        },
    )

    assert len(result) == 1
    assert result[0].anomaly_type == AnomalyType.PAYMENT_DROP


def test_settlement_variance_is_detected():
    result = detect_revenue_anomalies(
        settlements=[
            {
                "settlement_id": "s1",
                "expected_amount": 100000,
                "amount": 90000,
            }
        ]
    )

    assert len(result) == 1
    assert (
        result[0].anomaly_type
        == AnomalyType.SETTLEMENT_VARIANCE
    )
    assert result[0].variance == -10000


def test_anomaly_summary_is_read_only():
    anomalies = detect_revenue_anomalies(
        refunds=[
            {
                "refund_id": "r1",
                "amount": 300000,
            }
        ],
        baselines={
            "refund_amount": 100000,
        },
    )

    report = summarize_revenue_anomalies(anomalies)

    assert report.total_anomalies == 1
    assert report.high_or_critical_count == 1
    assert report.human_review_required is True
    assert report.read_only is True
    assert report.financial_mutation is False
    assert report.provider_mutation is False
