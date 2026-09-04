from revenex.intelligence import build_intelligence_snapshot


def test_intelligence_pipeline_connects_forecast_anomaly_root_cause():
    result = build_intelligence_snapshot(
        historical_revenue=[
            100000,
            110000,
            120000,
        ],
        current_revenue=60000,
        expected_revenue=120000,
        actual_revenue=60000,
        unpaid_invoices=[
            {
                "invoice_id": "i1",
                "amount": 60000,
            }
        ],
    )

    assert result.forecast_available is True
    assert result.forecast is not None
    assert result.forecast.projected_revenue == 130000.0

    assert result.anomaly_count == 1
    assert result.primary_anomaly is not None

    assert result.root_cause_count == 1
    assert result.primary_root_cause is not None

    assert result.executive_signal == "HIGH_REVENUE_RISK"
    assert result.human_review_required is True
    assert result.read_only is True
    assert result.financial_mutation is False
    assert result.provider_mutation is False


def test_intelligence_pipeline_handles_insufficient_data():
    result = build_intelligence_snapshot()

    assert result.forecast is None
    assert result.forecast_available is False
    assert result.anomaly_count == 0
    assert result.root_cause_count == 0
    assert result.executive_signal == "INSUFFICIENT_DATA"
    assert result.confidence == 0.0


def test_intelligence_pipeline_is_read_only():
    result = build_intelligence_snapshot(
        historical_revenue=[
            100000,
            110000,
        ],
        current_revenue=90000,
    )

    assert result.read_only is True
    assert result.human_review_required is True
    assert result.financial_mutation is False
    assert result.provider_mutation is False

def test_p2_adapter_isolated_and_read_only():
    from revenex.intelligence.p2_integration import build_p2_intelligence

    result = build_p2_intelligence(
        invoices=[],
        payments=[],
    )

    assert set(result) == {
        "revenue_graph",
        "leakage",
        "anomalies",
        "root_causes",
        "forecast",
        "safety",
    }

    assert result["safety"]["read_only"] is True
    assert result["safety"]["execution_allowed"] is False
    assert result["safety"]["automatic_action"] is False
    assert result["safety"]["financial_mutation"] is False
    assert result["safety"]["provider_mutation"] is False

    assert (
        result["forecast"]["forecast"]["trend"]
        == "INSUFFICIENT_DATA"
    )

    assert result["forecast"]["forecast"]["confidence"] == 0.0
    assert result["anomalies"]["total_anomalies"] == 0

