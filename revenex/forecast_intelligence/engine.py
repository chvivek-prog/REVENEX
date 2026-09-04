"""REVENEX Phase 28 — Revenue Forecast Intelligence.

Deterministic, explainable revenue forecasting based only on
supplied historical observations.

Read-only:
- no financial mutation
- no provider mutation
- no automatic execution
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ForecastHorizon(str, Enum):
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    LONG_TERM = "LONG_TERM"


class ForecastRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class RevenueForecast:
    forecast_id: str
    horizon: ForecastHorizon
    projected_revenue: float
    lower_bound: float
    upper_bound: float
    confidence: float
    risk: ForecastRisk
    trend: str
    evidence: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class ForecastReport:
    forecasts: tuple[RevenueForecast, ...]
    total_forecasts: int
    projected_revenue: float
    average_confidence: float
    high_risk_count: int
    human_review_required: bool
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _confidence(value: float) -> float:
    return max(
        0.0,
        min(
            1.0,
            round(value, 4),
        ),
    )


def _trend(values: list[float]) -> str:
    if len(values) < 2:
        return "INSUFFICIENT_DATA"

    previous = values[-2]
    current = values[-1]

    if current > previous:
        return "UPWARD"

    if current < previous:
        return "DOWNWARD"

    return "STABLE"


def forecast_revenue(
    *,
    historical_revenue: list[float]
    | tuple[float, ...]
    | None = None,
    horizon: ForecastHorizon = ForecastHorizon.SHORT_TERM,
    forecast_id: str = "revenue-forecast",
) -> RevenueForecast:
    """Produce a deterministic revenue projection.

    Uses the supplied historical series only. No external provider
    calls and no financial state mutation occur.
    """

    values = [
        _money(value)
        for value in (historical_revenue or [])
    ]

    if not values:
        return RevenueForecast(
            forecast_id=forecast_id,
            horizon=horizon,
            projected_revenue=0.0,
            lower_bound=0.0,
            upper_bound=0.0,
            confidence=0.0,
            risk=ForecastRisk.HIGH,
            trend="INSUFFICIENT_DATA",
            evidence=(
                "historical_observations=0",
                "forecast_status=INSUFFICIENT_DATA",
            ),
        )

    if len(values) == 1:
        projected = values[0]
        confidence = 0.50
        volatility = 0.0
    else:
        recent = values[-1]
        previous = values[-2]

        # Phase 28 forecasting contract:
        # extrapolate the latest absolute revenue delta.
        #
        # Example:
        # 100k -> 110k -> 120k
        # latest delta = +10k
        # forecast = 120k + 10k = 130k
        delta = recent - previous

        projected = recent + delta

        mean = sum(values) / len(values)

        variance = (
            sum(
                (value - mean) ** 2
                for value in values
            )
            / len(values)
        )

        volatility = (
            variance ** 0.5
            / mean
            if mean != 0
            else 1.0
        )

        confidence = _confidence(
            max(
                0.35,
                min(
                    0.95,
                    0.90 - volatility,
                ),
            )
        )

    uncertainty = abs(projected) * max(
        0.05,
        volatility,
    )

    lower = max(
        0.0,
        projected - uncertainty,
    )

    upper = projected + uncertainty

    if volatility >= 0.30:
        risk = ForecastRisk.HIGH
    elif volatility >= 0.15:
        risk = ForecastRisk.MEDIUM
    else:
        risk = ForecastRisk.LOW

    return RevenueForecast(
        forecast_id=forecast_id,
        horizon=horizon,
        projected_revenue=round(projected, 2),
        lower_bound=round(lower, 2),
        upper_bound=round(upper, 2),
        confidence=confidence,
        risk=risk,
        trend=_trend(values),
        evidence=(
            f"historical_observations={len(values)}",
            f"latest_revenue={values[-1]:.2f}",
            f"latest_delta={values[-1] - values[-2]:.2f}",
            "forecast_method=latest_delta_extrapolation",
            f"projected_revenue={projected:.2f}",
            f"volatility={volatility:.4f}",
            f"trend={_trend(values)}",
        ),
    )


def summarize_forecast(
    forecasts: list[RevenueForecast]
    | tuple[RevenueForecast, ...],
) -> ForecastReport:
    forecasts = tuple(forecasts)

    total = sum(
        forecast.projected_revenue
        for forecast in forecasts
    )

    average_confidence = (
        sum(
            forecast.confidence
            for forecast in forecasts
        )
        / len(forecasts)
        if forecasts
        else 0.0
    )

    high_risk = sum(
        1
        for forecast in forecasts
        if forecast.risk == ForecastRisk.HIGH
    )

    return ForecastReport(
        forecasts=forecasts,
        total_forecasts=len(forecasts),
        projected_revenue=round(total, 2),
        average_confidence=round(
            average_confidence,
            4,
        ),
        high_risk_count=high_risk,
        human_review_required=bool(forecasts),
        read_only=True,
        financial_mutation=False,
        provider_mutation=False,
    )
