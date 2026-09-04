from revenex.anomaly_intelligence import (
    AnomalySeverity,
    AnomalyType,
    detect_revenue_anomalies,
    summarize_anomalies,
)


def test_revenue_drop_is_detected():
    anomalies = detect_revenue_anomalies(
        historical_revenue=[100000, 100000, 100000],
        current_revenue=70000,
    )

    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == AnomalyType.REVENUE_DROP
    assert anomalies[0].severity == AnomalySeverity.HIGH
    assert anomalies[0].read_only is True
    assert anomalies[0].financial_mutation is False
    assert anomalies[0].provider_mutation is False


def test_revenue_spike_is_detected():
    anomalies = detect_revenue_anomalies(
        historical_revenue=[100000, 100000, 100000],
        current_revenue=150000,
    )

    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == AnomalyType.REVENUE_SPIKE


def test_normal_revenue_is_not_anomaly():
    anomalies = detect_revenue_anomalies(
        historical_revenue=[100000, 100000, 100000],
        current_revenue=110000,
    )

    assert len(anomalies) == 0


def test_multiple_revenue_signals():
    anomalies = detect_revenue_anomalies(
        historical_revenue=[100000, 100000, 100000],
        historical_collections=[80000, 80000, 80000],
        historical_payments=[90000, 90000, 90000],
        current_revenue=70000,
        current_collection=60000,
        current_payment=70000,
    )

    assert len(anomalies) == 3


def test_anomaly_summary_is_safe():
    anomalies = detect_revenue_anomalies(
        historical_revenue=[100000, 100000, 100000],
        current_revenue=50000,
    )

    report = summarize_anomalies(anomalies)

    assert report.total_anomalies == 1
    assert report.high_count == 1
    assert report.human_review_required is True
    assert report.read_only is True
    assert report.financial_mutation is False
    assert report.provider_mutation is False
