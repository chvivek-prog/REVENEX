"""
REVENEX Stage 35 — Revenue Risk Intelligence.

Aggregates customer-level predictions into an executive-level
revenue risk view.

Read-only. Deterministic. No provider or financial mutation.
"""

from dataclasses import dataclass
from typing import Any

from revenex.prediction.revenue_predictor import (
    RevenuePrediction,
    predict_all_customers,
)


@dataclass(frozen=True)
class CustomerRisk:
    customer_id: str
    revenue_at_risk: float
    late_payment_risk: float
    payment_probability: float
    confidence: float
    severity: str


@dataclass(frozen=True)
class RevenueRiskReport:
    total_outstanding: float
    expected_collection: float
    total_revenue_at_risk: float
    high_risk_exposure: float
    critical_risk_exposure: float
    high_risk_customer_count: int
    critical_customer_count: int
    concentration_ratio: float
    customer_risks: tuple[CustomerRisk, ...]
    executive_summary: str


def _severity(prediction: RevenuePrediction) -> str:
    risk = prediction.late_payment_risk
    exposure = prediction.revenue_at_risk

    if risk >= 0.80 and exposure > 0:
        return "CRITICAL"

    if risk >= 0.60 and exposure > 0:
        return "HIGH"

    if risk >= 0.35 and exposure > 0:
        return "MEDIUM"

    return "LOW"


def build_customer_risk(
    prediction: RevenuePrediction,
) -> CustomerRisk:
    return CustomerRisk(
        customer_id=prediction.customer_id,
        revenue_at_risk=prediction.revenue_at_risk,
        late_payment_risk=prediction.late_payment_risk,
        payment_probability=prediction.payment_probability,
        confidence=prediction.confidence,
        severity=_severity(prediction),
    )


def build_revenue_risk_report(
    invoices: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> RevenueRiskReport:
    predictions = predict_all_customers(
        invoices,
        payments,
    )

    customer_risks = tuple(
        build_customer_risk(prediction)
        for prediction in predictions
    )

    total_outstanding = sum(
        float(
            invoice.get(
                "outstanding_amount",
                invoice.get("balance", 0),
            )
            or 0
        )
        for invoice in invoices
    )

    expected_collection = sum(
        prediction.expected_collection
        for prediction in predictions
    )

    total_revenue_at_risk = sum(
        prediction.revenue_at_risk
        for prediction in predictions
    )

    high_risk_exposure = sum(
        risk.revenue_at_risk
        for risk in customer_risks
        if risk.severity in {"HIGH", "CRITICAL"}
    )

    critical_risk_exposure = sum(
        risk.revenue_at_risk
        for risk in customer_risks
        if risk.severity == "CRITICAL"
    )

    high_risk_customer_count = sum(
        1
        for risk in customer_risks
        if risk.severity in {"HIGH", "CRITICAL"}
    )

    critical_customer_count = sum(
        1
        for risk in customer_risks
        if risk.severity == "CRITICAL"
    )

    concentration_ratio = (
        high_risk_exposure / total_revenue_at_risk
        if total_revenue_at_risk > 0
        else 0.0
    )

    if critical_customer_count:
        executive_summary = (
            f"{critical_customer_count} critical customer risk "
            f"exposure(s) require immediate review. "
            f"Total revenue at risk is "
            f"₹{total_revenue_at_risk:,.2f}."
        )
    elif high_risk_customer_count:
        executive_summary = (
            f"{high_risk_customer_count} high-priority customer "
            f"risk exposure(s) require review. "
            f"Total revenue at risk is "
            f"₹{total_revenue_at_risk:,.2f}."
        )
    elif total_revenue_at_risk > 0:
        executive_summary = (
            "Revenue risk is present but below the high-risk "
            "threshold. Total revenue at risk is "
            f"₹{total_revenue_at_risk:,.2f}."
        )
    else:
        executive_summary = (
            "No material revenue risk was detected by the "
            "current deterministic risk model."
        )

    return RevenueRiskReport(
        total_outstanding=total_outstanding,
        expected_collection=expected_collection,
        total_revenue_at_risk=total_revenue_at_risk,
        high_risk_exposure=high_risk_exposure,
        critical_risk_exposure=critical_risk_exposure,
        high_risk_customer_count=high_risk_customer_count,
        critical_customer_count=critical_customer_count,
        concentration_ratio=concentration_ratio,
        customer_risks=customer_risks,
        executive_summary=executive_summary,
    )


def rank_customer_risks(
    report: RevenueRiskReport,
) -> tuple[CustomerRisk, ...]:
    return tuple(
        sorted(
            report.customer_risks,
            key=lambda risk: (
                risk.revenue_at_risk,
                risk.late_payment_risk,
            ),
            reverse=True,
        )
    )
