"""REVENEX Phase 26 — Revenue Anomaly Intelligence.

Read-only anomaly detection across revenue lifecycle data.
No financial/provider mutation is permitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyType(str, Enum):
    PAYMENT_SPIKE = "PAYMENT_SPIKE"
    PAYMENT_DROP = "PAYMENT_DROP"
    COLLECTION_DROP = "COLLECTION_DROP"
    SETTLEMENT_DELAY = "SETTLEMENT_DELAY"
    SETTLEMENT_VARIANCE = "SETTLEMENT_VARIANCE"
    REFUND_SPIKE = "REFUND_SPIKE"
    DISPUTE_SPIKE = "DISPUTE_SPIKE"


@dataclass(frozen=True)
class RevenueAnomaly:
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    entity_type: str
    entity_id: str
    observed_value: float
    baseline_value: float
    variance: float
    explanation: str
    evidence: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class AnomalyReport:
    anomalies: tuple[RevenueAnomaly, ...]
    total_anomalies: int
    high_or_critical_count: int
    total_exposure: float
    human_review_required: bool
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _anomaly(
    *,
    anomaly_type: AnomalyType,
    severity: AnomalySeverity,
    entity_type: str,
    entity_id: str,
    observed: float,
    baseline: float,
    explanation: str,
    evidence: tuple[str, ...],
) -> RevenueAnomaly:
    variance = observed - baseline

    return RevenueAnomaly(
        anomaly_id=f"{anomaly_type.value}:{entity_type}:{entity_id}",
        anomaly_type=anomaly_type,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        observed_value=observed,
        baseline_value=baseline,
        variance=variance,
        explanation=explanation,
        evidence=evidence,
    )


def detect_revenue_anomalies(
    *,
    payments: list[dict[str, Any]] | None = None,
    refunds: list[dict[str, Any]] | None = None,
    disputes: list[dict[str, Any]] | None = None,
    settlements: list[dict[str, Any]] | None = None,
    baselines: dict[str, float] | None = None,
) -> tuple[RevenueAnomaly, ...]:
    """Detect deterministic revenue anomalies.

    The engine deliberately uses explicit supplied baselines.
    It does not mutate data, call providers, or execute actions.
    """

    payments = payments or []
    refunds = refunds or []
    disputes = disputes or []
    settlements = settlements or []
    baselines = baselines or {}

    anomalies: list[RevenueAnomaly] = []

    payment_baseline = _money(
        baselines.get("payment_amount")
    )

    for payment in payments:
        payment_id = str(
            payment.get(
                "payment_id",
                payment.get("id", ""),
            )
        )

        if not payment_id:
            continue

        observed = _money(payment.get("amount"))

        if payment_baseline > 0:
            ratio = observed / payment_baseline

            if ratio >= 2.0:
                anomalies.append(
                    _anomaly(
                        anomaly_type=AnomalyType.PAYMENT_SPIKE,
                        severity=AnomalySeverity.HIGH,
                        entity_type="payment",
                        entity_id=payment_id,
                        observed=observed,
                        baseline=payment_baseline,
                        explanation=(
                            "Payment amount materially exceeds "
                            "the supplied revenue baseline."
                        ),
                        evidence=(
                            f"observed={observed:.2f}",
                            f"baseline={payment_baseline:.2f}",
                            f"ratio={ratio:.4f}",
                        ),
                    )
                )
            elif ratio <= 0.5:
                anomalies.append(
                    _anomaly(
                        anomaly_type=AnomalyType.PAYMENT_DROP,
                        severity=AnomalySeverity.MEDIUM,
                        entity_type="payment",
                        entity_id=payment_id,
                        observed=observed,
                        baseline=payment_baseline,
                        explanation=(
                            "Payment amount is materially below "
                            "the supplied revenue baseline."
                        ),
                        evidence=(
                            f"observed={observed:.2f}",
                            f"baseline={payment_baseline:.2f}",
                            f"ratio={ratio:.4f}",
                        ),
                    )
                )

    refund_baseline = _money(
        baselines.get("refund_amount")
    )

    for refund in refunds:
        refund_id = str(
            refund.get(
                "refund_id",
                refund.get("id", ""),
            )
        )

        if not refund_id or refund_baseline <= 0:
            continue

        observed = _money(refund.get("amount"))

        if observed >= refund_baseline * 2:
            anomalies.append(
                _anomaly(
                    anomaly_type=AnomalyType.REFUND_SPIKE,
                    severity=AnomalySeverity.HIGH,
                    entity_type="refund",
                    entity_id=refund_id,
                    observed=observed,
                    baseline=refund_baseline,
                    explanation=(
                        "Refund amount materially exceeds "
                        "the supplied refund baseline."
                    ),
                    evidence=(
                        f"observed={observed:.2f}",
                        f"baseline={refund_baseline:.2f}",
                    ),
                )
            )

    dispute_baseline = _money(
        baselines.get("dispute_amount")
    )

    for dispute in disputes:
        dispute_id = str(
            dispute.get(
                "dispute_id",
                dispute.get("id", ""),
            )
        )

        if not dispute_id or dispute_baseline <= 0:
            continue

        observed = _money(dispute.get("amount"))

        if observed >= dispute_baseline * 2:
            anomalies.append(
                _anomaly(
                    anomaly_type=AnomalyType.DISPUTE_SPIKE,
                    severity=AnomalySeverity.HIGH,
                    entity_type="dispute",
                    entity_id=dispute_id,
                    observed=observed,
                    baseline=dispute_baseline,
                    explanation=(
                        "Dispute amount materially exceeds "
                        "the supplied dispute baseline."
                    ),
                    evidence=(
                        f"observed={observed:.2f}",
                        f"baseline={dispute_baseline:.2f}",
                    ),
                )
            )

    settlement_baseline = _money(
        baselines.get("settlement_amount")
    )

    for settlement in settlements:
        settlement_id = str(
            settlement.get(
                "settlement_id",
                settlement.get("id", ""),
            )
        )

        if not settlement_id:
            continue

        observed = _money(
            settlement.get("amount")
        )

        expected = _money(
            settlement.get(
                "expected_amount",
                settlement_baseline,
            )
        )

        if expected > 0 and observed < expected:
            gap = expected - observed

            anomalies.append(
                _anomaly(
                    anomaly_type=(
                        AnomalyType.SETTLEMENT_VARIANCE
                    ),
                    severity=(
                        AnomalySeverity.HIGH
                        if gap / expected >= 0.10
                        else AnomalySeverity.MEDIUM
                    ),
                    entity_type="settlement",
                    entity_id=settlement_id,
                    observed=observed,
                    baseline=expected,
                    explanation=(
                        "Settlement amount is below the "
                        "expected settlement amount."
                    ),
                    evidence=(
                        f"expected={expected:.2f}",
                        f"observed={observed:.2f}",
                        f"gap={gap:.2f}",
                    ),
                )
            )

    return tuple(anomalies)


def summarize_revenue_anomalies(
    anomalies: list[RevenueAnomaly]
    | tuple[RevenueAnomaly, ...],
) -> AnomalyReport:
    anomalies = tuple(anomalies)

    high_or_critical = sum(
        1
        for anomaly in anomalies
        if anomaly.severity
        in (
            AnomalySeverity.HIGH,
            AnomalySeverity.CRITICAL,
        )
    )

    exposure = sum(
        max(
            abs(anomaly.variance),
            0.0,
        )
        for anomaly in anomalies
    )

    return AnomalyReport(
        anomalies=anomalies,
        total_anomalies=len(anomalies),
        high_or_critical_count=high_or_critical,
        total_exposure=exposure,
        human_review_required=bool(anomalies),
        read_only=True,
        financial_mutation=False,
        provider_mutation=False,
    )
