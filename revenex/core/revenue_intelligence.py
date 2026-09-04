"""
REVENEX Stage 31 — Revenue Intelligence Contract.

Canonical read-only intelligence pipeline:

OBSERVE
    ↓
INVESTIGATE
    ↓
PREDICT
    ↓
SIMULATE
    ↓
DECIDE
    ↓
AUDIT

This module contains deterministic, side-effect-free contracts.
No provider mutation, payment mutation, refund, or automatic
financial action is permitted here.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntelligenceStage(str, Enum):
    OBSERVE = "OBSERVE"
    INVESTIGATE = "INVESTIGATE"
    PREDICT = "PREDICT"
    SIMULATE = "SIMULATE"
    DECIDE = "DECIDE"
    AUDIT = "AUDIT"


@dataclass(frozen=True)
class RevenueState:
    invoices: tuple[dict[str, Any], ...] = ()
    payments: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class Finding:
    entity_id: str
    risk_score: float
    reason: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class Prediction:
    value: float | None
    confidence: float
    basis: tuple[str, ...] = ()


@dataclass(frozen=True)
class Simulation:
    scenario: str
    expected_collection: float
    confidence: float


@dataclass(frozen=True)
class Decision:
    priority: str
    recommended_action: str
    risk_score: float
    confidence: float
    reason: str
    requires_approval: bool = True


@dataclass(frozen=True)
class AuditTrace:
    stages_completed: tuple[str, ...]
    read_only: bool = True
    automatic_action: bool = False
    provider_mutation: bool = False
    financial_mutation: bool = False


@dataclass(frozen=True)
class IntelligenceResult:
    stages: dict[str, Any]
    execution: dict[str, bool]


def observe(state: RevenueState) -> RevenueState:
    """Return the observed revenue state without mutation."""
    return state


def investigate(state: RevenueState) -> tuple[Finding, ...]:
    """Identify deterministic revenue-risk findings."""
    findings: list[Finding] = []

    for invoice in state.invoices:
        outstanding = float(
            invoice.get("outstanding_amount", invoice.get("amount", 0)) or 0
        )
        overdue = int(invoice.get("days_overdue", 0) or 0)

        if outstanding > 0 and overdue > 30:
            risk_score = min(
                1.0,
                0.50 + min(overdue / 180.0, 0.30)
                + min(outstanding / 1_000_000.0, 0.20),
            )

            findings.append(
                Finding(
                    entity_id=str(
                        invoice.get("invoice_id", invoice.get("id", "unknown"))
                    ),
                    risk_score=risk_score,
                    reason="Outstanding invoice is more than 30 days overdue.",
                    evidence=(
                        f"outstanding_amount={outstanding}",
                        f"days_overdue={overdue}",
                    ),
                )
            )

    return tuple(findings)


def predict(
    state: RevenueState,
    findings: tuple[Finding, ...],
) -> Prediction:
    """Produce a transparent baseline prediction."""
    total_outstanding = sum(
        float(
            invoice.get(
                "outstanding_amount",
                invoice.get("amount", 0),
            )
            or 0
        )
        for invoice in state.invoices
    )

    confidence = (
        min(1.0, 0.50 + (0.10 * len(findings)))
        if state.invoices
        else 0.0
    )

    return Prediction(
        value=total_outstanding,
        confidence=confidence,
        basis=(
            "current invoice outstanding balances",
            "deterministic overdue-risk findings",
        ),
    )


def simulate(
    prediction: Prediction,
    findings: tuple[Finding, ...],
) -> tuple[Simulation, ...]:
    """Compare read-only recovery scenarios."""
    expected = float(prediction.value or 0)

    risk = (
        max((finding.risk_score for finding in findings), default=0.0)
    )

    return (
        Simulation(
            scenario="STANDARD",
            expected_collection=expected * 0.60,
            confidence=max(0.0, prediction.confidence - 0.05),
        ),
        Simulation(
            scenario="PRIORITY",
            expected_collection=expected * (0.65 + (risk * 0.10)),
            confidence=min(1.0, prediction.confidence + 0.05),
        ),
    )


def decide(
    findings: tuple[Finding, ...],
    simulations: tuple[Simulation, ...],
) -> Decision:
    """Generate an advisory decision; never execute it."""
    risk = max(
        (finding.risk_score for finding in findings),
        default=0.0,
    )

    best = max(
        simulations,
        key=lambda simulation: simulation.expected_collection,
        default=None,
    )

    if risk >= 0.80:
        priority = "CRITICAL"
    elif risk >= 0.70:
        priority = "HIGH"
    elif risk >= 0.50:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    action = (
        "PRIORITY_RECOVERY"
        if best and risk >= 0.70
        else "STANDARD_RECOVERY"
        if best and risk >= 0.50
        else "MONITOR"
    )

    return Decision(
        priority=priority,
        recommended_action=action,
        risk_score=risk,
        confidence=best.confidence if best else 0.0,
        reason=(
            "Decision derived from observed revenue state, "
            "risk findings and read-only simulation."
        ),
        requires_approval=True,
    )


def audit(
    findings: tuple[Finding, ...],
    prediction: Prediction,
    simulations: tuple[Simulation, ...],
    decision: Decision,
) -> AuditTrace:
    """Create an immutable description of the completed pipeline."""
    return AuditTrace(
        stages_completed=tuple(
            stage.value for stage in IntelligenceStage
        )
    )


def run_revenue_intelligence(
    state: RevenueState,
) -> IntelligenceResult:
    """
    Canonical Stage 31 pipeline.

    This function is strictly advisory and read-only.
    """
    observed = observe(state)
    findings = investigate(observed)
    prediction = predict(observed, findings)
    simulations = simulate(prediction, findings)
    decision = decide(findings, simulations)
    audit_trace = audit(
        findings,
        prediction,
        simulations,
        decision,
    )

    return IntelligenceResult(
        stages={
            IntelligenceStage.OBSERVE.value: observed,
            IntelligenceStage.INVESTIGATE.value: findings,
            IntelligenceStage.PREDICT.value: prediction,
            IntelligenceStage.SIMULATE.value: simulations,
            IntelligenceStage.DECIDE.value: decision,
            IntelligenceStage.AUDIT.value: audit_trace,
        },
        execution={
            "read_only": True,
            "automatic_action": False,
            "provider_mutation": False,
            "financial_mutation": False,
        },
    )
