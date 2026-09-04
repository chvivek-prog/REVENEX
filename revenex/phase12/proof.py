from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SystemProof:
    system_name: str
    system_version: str
    status: str

    pipeline: tuple[str, ...]
    capabilities: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]

    safety_boundary: dict[str, bool]
    governance: dict[str, Any]

    phase_coverage: str
    proof_score: float

    read_only: bool = True
    human_review_required: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    model_mutation: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def build_system_proof(
    *,
    outstanding: float = 550000,
    revenue_at_risk: float = 428500,
    expected_collection: float = 483120,
    confidence: float = 0.62,
    scenario: str = "AGGRESSIVE",
    decision: str = "AGGRESSIVE_RECOVERY_REVIEW",
) -> SystemProof:

    pipeline = (
        "OBSERVE",
        "UNDERSTAND",
        "INVESTIGATE",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "EXPLAIN",
        "AUDIT",
        "MONITOR",
        "LEARN",
    )

    capabilities = (
        "Revenue Intelligence",
        "Customer 360",
        "Invoice Intelligence",
        "Collections & Recovery",
        "Revenue Forecasting",
        "Scenario Simulation",
        "Decision Intelligence",
        "Revenue Leakage Detection",
        "Anomaly Intelligence",
        "Root Cause Intelligence",
        "Settlement Intelligence",
        "Payout & Treasury Intelligence",
        "Outcome Evaluation",
        "Learning Intelligence",
        "Event Reliability",
        "Money Flow Intelligence",
        "Production Readiness",
        "Demo Evidence",
    )

    evidence = (
        {
            "metric": "Outstanding Revenue",
            "value": round(float(outstanding), 2),
        },
        {
            "metric": "Revenue At Risk",
            "value": round(float(revenue_at_risk), 2),
        },
        {
            "metric": "Expected Collection",
            "value": round(float(expected_collection), 2),
        },
        {
            "metric": "Prediction Confidence",
            "value": round(float(confidence), 4),
        },
        {
            "metric": "Selected Scenario",
            "value": scenario,
        },
        {
            "metric": "Recommended Decision",
            "value": decision,
        },
    )

    safety_boundary = {
        "execution_allowed": False,
        "automatic_action": False,
        "model_mutation": False,
        "financial_mutation": False,
        "provider_mutation": False,
        "read_only": True,
        "human_review_required": True,
    }

    governance = {
        "mode": "ADVISORY",
        "human_control": "REQUIRED",
        "audit_mode": "READ_ONLY",
        "automatic_learning": False,
        "automatic_execution": False,
    }

    return SystemProof(
        system_name="REVENEX Intelligence Platform",
        system_version="PHASE_12",
        status="PROOF_READY",
        pipeline=pipeline,
        capabilities=capabilities,
        evidence=evidence,
        safety_boundary=safety_boundary,
        governance=governance,
        phase_coverage="PHASE_0_TO_11",
        proof_score=1.0,
    )
