from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DemoEvidence:
    name: str
    value: Any
    explanation: str


@dataclass(frozen=True)
class DemoReport:
    title: str
    narrative: str
    evidence: tuple[DemoEvidence, ...]
    pipeline: tuple[str, ...]
    safety: dict[str, bool]
    demo_ready: bool
    read_only: bool
    human_review_required: bool


def generate_demo_report(
    *,
    outstanding: float = 550000,
    revenue_at_risk: float = 428500,
    expected_collection: float = 483120,
    confidence: float = 0.62,
    scenario: str = "AGGRESSIVE",
    decision: str = "AGGRESSIVE_RECOVERY_REVIEW",
) -> DemoReport:
    evidence = (
        DemoEvidence(
            "Outstanding Revenue",
            outstanding,
            "Current revenue exposure requiring intelligence.",
        ),
        DemoEvidence(
            "Revenue At Risk",
            revenue_at_risk,
            "Exposure identified for investigation and review.",
        ),
        DemoEvidence(
            "Expected Collection",
            expected_collection,
            "Predicted collection under the selected scenario.",
        ),
        DemoEvidence(
            "Confidence",
            confidence,
            "Deterministic confidence associated with the prediction.",
        ),
        DemoEvidence(
            "Scenario",
            scenario,
            "Selected advisory simulation scenario.",
        ),
        DemoEvidence(
            "Decision",
            decision,
            "Recommended decision requiring human approval.",
        ),
    )

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

    safety = {
        "execution_allowed": False,
        "automatic_action": False,
        "financial_mutation": False,
        "provider_mutation": False,
        "model_mutation": False,
        "human_review_required": True,
        "read_only": True,
    }

    narrative = (
        "REVENEX converts fragmented revenue signals into an "
        "explainable decision workflow. It observes exposure, "
        "investigates risk, predicts collection, simulates "
        "scenarios, recommends a decision, explains the evidence, "
        "audits the reasoning, and waits for real-world outcomes "
        "before learning. The system remains advisory and "
        "human-controlled."
    )

    return DemoReport(
        title="REVENEX Intelligence Platform",
        narrative=narrative,
        evidence=evidence,
        pipeline=pipeline,
        safety=safety,
        demo_ready=True,
        read_only=True,
        human_review_required=True,
    )
