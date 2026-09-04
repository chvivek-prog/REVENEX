from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from revenex.anomaly_intelligence import (
    Anomaly,
    detect_revenue_anomalies,
)
from revenex.forecast_intelligence import (
    RevenueForecast,
    forecast_revenue,
)
from revenex.root_cause_intelligence import (
    RootCause,
    analyze_root_causes,
)


@dataclass(frozen=True)
class IntelligenceSnapshot:
    forecast: RevenueForecast | None
    anomalies: tuple[Anomaly, ...]
    root_causes: tuple[RootCause, ...]

    forecast_available: bool
    anomaly_count: int
    root_cause_count: int

    primary_anomaly: Anomaly | None
    primary_root_cause: RootCause | None

    executive_signal: str
    confidence: float

    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


def _confidence(
    forecast: RevenueForecast | None,
    anomalies: tuple[Anomaly, ...],
    causes: tuple[RootCause, ...],
) -> float:
    values: list[float] = []

    if forecast is not None:
        values.append(float(forecast.confidence))

    values.extend(float(item.confidence) for item in causes)

    if not values:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            sum(values) / len(values),
        ),
    )


def _signal(
    *,
    forecast: RevenueForecast | None,
    anomalies: tuple[Anomaly, ...],
    causes: tuple[RootCause, ...],
) -> str:
    if not forecast and not anomalies and not causes:
        return "INSUFFICIENT_DATA"

    if any(
        item.severity.value == "CRITICAL"
        for item in anomalies
    ):
        return "CRITICAL_REVENUE_SIGNAL"

    if any(
        item.severity.value == "HIGH"
        for item in anomalies
    ):
        return "HIGH_REVENUE_RISK"

    if causes:
        if causes[0].category.value == "UNKNOWN":
            return "ROOT_CAUSE_UNCERTAIN"

        return "ROOT_CAUSE_IDENTIFIED"

    if forecast is not None:
        trend = forecast.trend
        trend = (
            trend.value
            if hasattr(trend, "value")
            else str(trend)
        )

        if trend == "UPWARD":
            return "REVENUE_GROWTH_SIGNAL"

        if trend == "DOWNWARD":
            return "REVENUE_DECLINE_SIGNAL"

        return "REVENUE_STABLE"

    return "REVENUE_MONITOR"


def build_intelligence_snapshot(
    *,
    historical_revenue: list[float] | None = None,
    current_revenue: float | None = None,
    historical_collections: list[float] | None = None,
    current_collection: float | None = None,
    historical_payments: list[float] | None = None,
    current_payment: float | None = None,
    historical_settlements: list[float] | None = None,
    current_settlement: float | None = None,
    expected_revenue: float | None = None,
    actual_revenue: float | None = None,
    unpaid_invoices: list[dict[str, Any]] | None = None,
    payment_failures: list[dict[str, Any]] | None = None,
    settlement_gaps: list[dict[str, Any]] | None = None,
    refunds: list[dict[str, Any]] | None = None,
    disputes: list[dict[str, Any]] | None = None,
    subscription_failures: list[dict[str, Any]] | None = None,
) -> IntelligenceSnapshot:

    history = historical_revenue or []

    forecast = (
        forecast_revenue(
            historical_revenue=history,
        )
        if len(history) >= 2
        else None
    )

    anomalies = detect_revenue_anomalies(
        historical_revenue=historical_revenue,
        historical_collections=historical_collections,
        historical_payments=historical_payments,
        historical_settlements=historical_settlements,
        current_revenue=current_revenue,
        current_collection=current_collection,
        current_payment=current_payment,
        current_settlement=current_settlement,
    )

    causes = analyze_root_causes(
        expected_revenue=expected_revenue,
        actual_revenue=actual_revenue,
        unpaid_invoices=unpaid_invoices,
        payment_failures=payment_failures,
        settlement_gaps=settlement_gaps,
        refunds=refunds,
        disputes=disputes,
        subscription_failures=subscription_failures,
    )

    signal = _signal(
        forecast=forecast,
        anomalies=anomalies,
        causes=causes,
    )

    return IntelligenceSnapshot(
        forecast=forecast,
        anomalies=anomalies,
        root_causes=causes,
        forecast_available=forecast is not None,
        anomaly_count=len(anomalies),
        root_cause_count=len(causes),
        primary_anomaly=anomalies[0] if anomalies else None,
        primary_root_cause=causes[0] if causes else None,
        executive_signal=signal,
        confidence=_confidence(
            forecast,
            anomalies,
            causes,
        ),
    )
