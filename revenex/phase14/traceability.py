from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source: str
    field: str
    value: Any
    role: str


@dataclass(frozen=True)
class TraceRecord:
    trace_id: str
    stage: str
    input_refs: tuple[str, ...]
    output: Any
    explanation: str
    human_review_required: bool = True
    read_only: bool = True


@dataclass(frozen=True)
class TraceabilityReport:
    status: str
    trace_id: str
    evidence: tuple[EvidenceItem, ...]
    records: tuple[TraceRecord, ...]
    chain_complete: bool
    evidence_complete: bool
    explanation_complete: bool
    governance_complete: bool
    traceability_score: float

    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    model_mutation: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _confidence(value: Any) -> float:
    try:
        return round(
            min(max(float(value or 0), 0.0), 1.0),
            4,
        )
    except (TypeError, ValueError):
        return 0.0


def build_traceability_report(
    *,
    trace_id: str = "trace-demo-001",
    outstanding: float = 550000,
    revenue_at_risk: float = 428500,
    expected_collection: float = 483120,
    confidence: float = 0.62,
    scenario: str = "AGGRESSIVE",
    decision: str = "AGGRESSIVE_RECOVERY_REVIEW",
) -> TraceabilityReport:

    evidence = (
        EvidenceItem(
            evidence_id="EV-001",
            source="revenue",
            field="outstanding",
            value=_money(outstanding),
            role="EXPOSURE",
        ),
        EvidenceItem(
            evidence_id="EV-002",
            source="risk",
            field="revenue_at_risk",
            value=_money(revenue_at_risk),
            role="RISK",
        ),
        EvidenceItem(
            evidence_id="EV-003",
            source="forecast",
            field="expected_collection",
            value=_money(expected_collection),
            role="PREDICTION",
        ),
        EvidenceItem(
            evidence_id="EV-004",
            source="simulation",
            field="confidence",
            value=_confidence(confidence),
            role="UNCERTAINTY",
        ),
        EvidenceItem(
            evidence_id="EV-005",
            source="simulation",
            field="scenario",
            value=scenario,
            role="SCENARIO",
        ),
        EvidenceItem(
            evidence_id="EV-006",
            source="decision",
            field="recommended_action",
            value=decision,
            role="DECISION",
        ),
    )

    records = (
        TraceRecord(
            trace_id=trace_id,
            stage="OBSERVE",
            input_refs=("EV-001",),
            output=_money(outstanding),
            explanation=(
                "Revenue exposure was observed from the supplied "
                "outstanding amount."
            ),
        ),
        TraceRecord(
            trace_id=trace_id,
            stage="UNDERSTAND",
            input_refs=("EV-001", "EV-002"),
            output=_money(revenue_at_risk),
            explanation=(
                "Observed exposure was interpreted alongside "
                "identified revenue risk."
            ),
        ),
        TraceRecord(
            trace_id=trace_id,
            stage="PREDICT",
            input_refs=("EV-001", "EV-002", "EV-003"),
            output=_money(expected_collection),
            explanation=(
                "Expected collection was produced as an advisory "
                "prediction."
            ),
        ),
        TraceRecord(
            trace_id=trace_id,
            stage="SIMULATE",
            input_refs=("EV-003", "EV-004", "EV-005"),
            output=scenario,
            explanation=(
                "The selected scenario represents an advisory "
                "simulation outcome."
            ),
        ),
        TraceRecord(
            trace_id=trace_id,
            stage="DECIDE",
            input_refs=("EV-002", "EV-003", "EV-004", "EV-005", "EV-006"),
            output=decision,
            explanation=(
                "The recommendation is derived from risk, "
                "prediction, confidence, and scenario evidence."
            ),
        ),
        TraceRecord(
            trace_id=trace_id,
            stage="GOVERN",
            input_refs=("EV-006",),
            output="HUMAN_REVIEW_REQUIRED",
            explanation=(
                "The recommendation remains advisory and requires "
                "human review before any future action."
            ),
        ),
    )

    required_stages = {
        "OBSERVE",
        "UNDERSTAND",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "GOVERN",
    }

    present_stages = {
        record.stage
        for record in records
    }

    referenced_evidence = {
        ref
        for record in records
        for ref in record.input_refs
    }

    evidence_ids = {
        item.evidence_id
        for item in evidence
    }

    chain_complete = required_stages.issubset(
        present_stages
    )

    evidence_complete = evidence_ids.issubset(
        referenced_evidence
    )

    explanation_complete = all(
        bool(record.explanation)
        for record in records
    )

    governance_complete = (
        all(
            record.human_review_required
            and record.read_only
            for record in records
        )
    )

    checks = (
        chain_complete,
        evidence_complete,
        explanation_complete,
        governance_complete,
    )

    score = round(
        sum(checks) / len(checks),
        4,
    )

    status = (
        "TRACEABILITY_VERIFIED"
        if all(checks)
        else "TRACEABILITY_REVIEW_REQUIRED"
    )

    return TraceabilityReport(
        status=status,
        trace_id=trace_id,
        evidence=evidence,
        records=records,
        chain_complete=chain_complete,
        evidence_complete=evidence_complete,
        explanation_complete=explanation_complete,
        governance_complete=governance_complete,
        traceability_score=score,
    )
