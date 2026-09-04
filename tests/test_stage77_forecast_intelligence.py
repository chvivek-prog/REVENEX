from revenex.forecast_intelligence import (
    ForecastHorizon,
    ForecastRisk,
    forecast_revenue,
    summarize_forecast,
)


def test_forecast_projects_upward_trend():
    result = forecast_revenue(
        historical_revenue=[
            100000,
            110000,
            120000,
        ],
        horizon=ForecastHorizon.SHORT_TERM,
    )

    assert result.projected_revenue == 130000.0
    assert result.trend == "UPWARD"
    assert result.confidence > 0
    assert result.read_only is True


def test_forecast_detects_downward_trend():
    result = forecast_revenue(
        historical_revenue=[
            150000,
            120000,
            90000,
        ]
    )

    assert result.projected_revenue == 60000.0
    assert result.trend == "DOWNWARD"


def test_forecast_handles_insufficient_data():
    result = forecast_revenue()

    assert result.projected_revenue == 0.0
    assert result.confidence == 0.0
    assert result.trend == "INSUFFICIENT_DATA"
    assert result.risk == ForecastRisk.HIGH
    assert result.human_review_required is True


def test_forecast_summary_is_safe():
    forecasts = [
        forecast_revenue(
            historical_revenue=[
                100000,
                110000,
            ]
        ),
        forecast_revenue(
            historical_revenue=[
                200000,
                210000,
            ]
        ),
    ]

    report = summarize_forecast(forecasts)

    assert report.total_forecasts == 2
    assert report.projected_revenue == 340000.0
    assert report.average_confidence > 0
    assert report.human_review_required is True
    assert report.read_only is True
    assert report.financial_mutation is False
    assert report.provider_mutation is False
