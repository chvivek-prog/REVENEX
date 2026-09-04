from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean, pstdev
from typing import Any


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyType(str, Enum):
    REVENUE_DROP = "REVENUE_DROP"
    REVENUE_SPIKE = "REVENUE_SPIKE"
    COLLECTION_DROP = "COLLECTION_DROP"
    PAYMENT_DROP = "PAYMENT_DROP"
    SETTLEMENT_DROP = "SETTLEMENT_DROP"


@dataclass(frozen=True)
class Anomaly:
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    entity_type: str
    entity_id: str
    expected_value: float
    observed_value: float
    deviation: float
    explanation: str
    evidence: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class RevenueAnomalyReport:
    anomalies: tuple[Anomaly, ...]
    total_anomalies: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_deviation: float
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _severity(deviation: float) -> AnomalySeverity:
    magnitude = abs(deviation)

    # Deterministic REVENEX anomaly severity contract:
    #
    # <15%       LOW
    # 15%–<30%   MEDIUM
    # 30%–50%    HIGH
    # >50%       CRITICAL
    #
    # Exactly 50% is intentionally HIGH because the Phase 29
    # contract treats a 50% revenue deviation as HIGH severity.

    if magnitude > 0.50:
        return AnomalySeverity.CRITICAL

    if magnitude >= 0.30:
        return AnomalySeverity.HIGH

    if magnitude >= 0.15:
        return AnomalySeverity.MEDIUM

    return AnomalySeverity.LOW


def _build_anomaly(
    *,
    anomaly_type: AnomalyType,
    entity_type: str,
    entity_id: str,
    expected: float,
    observed: float,
    explanation: str,
    evidence: tuple[str, ...],
) -> Anomaly:
    deviation = (
        (observed - expected) / expected
        if expected != 0
        else 0.0
    )

    return Anomaly(
        anomaly_id=f"{anomaly_type.value}:{entity_type}:{entity_id}",
        anomaly_type=anomaly_type,
        severity=_severity(deviation),
        entity_type=entity_type,
        entity_id=entity_id,
        expected_value=expected,
        observed_value=observed,
        deviation=deviation,
        explanation=explanation,
        evidence=evidence,
    )


def detect_revenue_anomalies(
    *,
    historical_revenue: list[float] | None = None,
    historical_collections: list[float] | None = None,
    historical_payments: list[float] | None = None,
    historical_settlements: list[float] | None = None,
    current_revenue: float | None = None,
    current_collection: float | None = None,
    current_payment: float | None = None,
    current_settlement: float | None = None,
) -> tuple[Anomaly, ...]:
    anomalies: list[Anomaly] = []

    def inspect(
        history: list[float] | None,
        current: float | None,
        anomaly_type: AnomalyType,
        entity_type: str,
        entity_id: str,
    ) -> None:
        if not history or current is None:
            return

        values = [_money(v) for v in history]

        if len(values) < 2:
            return

        expected = mean(values)
        observed = _money(current)

        if expected == 0:
            return

        deviation = (observed - expected) / expected

        # Anomaly threshold: 15% deviation from historical baseline.
        if abs(deviation) < 0.15:
            return

        actual_type = anomaly_type

        if deviation > 0:
            actual_type = (
                AnomalyType.REVENUE_SPIKE
                if anomaly_type == AnomalyType.REVENUE_DROP
                else anomaly_type
            )

        anomalies.append(
            _build_anomaly(
                anomaly_type=actual_type,
                entity_type=entity_type,
                entity_id=entity_id,
                expected=expected,
                observed=observed,
                explanation=(
                    f"Observed value deviates "
                    f"{abs(deviation) * 100:.2f}% "
                    f"from historical baseline."
                ),
                evidence=(
                    f"historical_mean={expected:.2f}",
                    f"observed={observed:.2f}",
                    f"deviation={deviation:.4f}",
                ),
            )
        )

    inspect(
        historical_revenue,
        current_revenue,
        AnomalyType.REVENUE_DROP,
        "revenue",
        "revenue",
    )

    inspect(
        historical_collections,
        current_collection,
        AnomalyType.COLLECTION_DROP,
        "collection",
        "collection",
    )

    inspect(
        historical_payments,
        current_payment,
        AnomalyType.PAYMENT_DROP,
        "payment",
        "payment",
    )

    inspect(
        historical_settlements,
        current_settlement,
        AnomalyType.SETTLEMENT_DROP,
        "settlement",
        "settlement",
    )

    return tuple(anomalies)


def summarize_anomalies(
    anomalies: list[Anomaly] | tuple[Anomaly, ...],
) -> RevenueAnomalyReport:
    items = tuple(anomalies)

    return RevenueAnomalyReport(
        anomalies=items,
        total_anomalies=len(items),
        critical_count=sum(
            a.severity == AnomalySeverity.CRITICAL
            for a in items
        ),
        high_count=sum(
            a.severity == AnomalySeverity.HIGH
            for a in items
        ),
        medium_count=sum(
            a.severity == AnomalySeverity.MEDIUM
            for a in items
        ),
        low_count=sum(
            a.severity == AnomalySeverity.LOW
            for a in items
        ),
        total_deviation=sum(
            abs(a.observed_value - a.expected_value)
            for a in items
        ),
    )
