from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DashboardProof:
    title: str
    state: str
    headline: str

    metrics: tuple[dict[str, Any], ...]
    intelligence_sections: tuple[str, ...]
    pipeline: tuple[str, ...]
    safety: dict[str, bool]
    governance: dict[str, Any]

    demo_sequence: tuple[str, ...]
    explanation: tuple[str, ...]

    read_only: bool = True
    human_review_required: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    model_mutation: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def build_dashboard_proof(
    *,
    outstanding: float = 550000,
    revenue_at_risk: float = 428500,
    expected_collection: float = 483120,
    confidence: float = 0.62,
    scenario: str = "AGGRESSIVE",
    decision: str = "AGGRESSIVE_RECOVERY_REVIEW",
) -> DashboardProof:

    metrics = (
        {
            "label": "OUTSTANDING REVENUE",
            "value": round(float(outstanding), 2),
        },
        {
            "label": "REVENUE AT RISK",
            "value": round(float(revenue_at_risk), 2),
        },
        {
            "label": "EXPECTED COLLECTION",
            "value": round(float(expected_collection), 2),
        },
        {
            "label": "AI CONFIDENCE",
            "value": round(float(confidence), 4),
        },
        {
            "label": "SCENARIO",
            "value": scenario,
        },
        {
            "label": "RECOMMENDED ACTION",
            "value": decision,
        },
    )

    intelligence_sections = (
        "Revenue Intelligence",
        "Customer 360",
        "Invoice Intelligence",
        "Collections & Recovery",
        "Revenue Forecast",
        "Scenario Simulation",
        "Decision Center",
        "Audit & Explainability",
        "Outcome Monitoring",
        "Learning Engine",
        "Settlement Intelligence",
        "Payout & Treasury Intelligence",
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
        "execution": "DISABLED",
        "automatic_learning": "DISABLED",
    }

    demo_sequence = (
        "1. Command Center",
        "2. Revenue Intelligence",
        "3. Customer 360",
        "4. Forecast",
        "5. Simulation",
        "6. Decision Center",
        "7. Audit & Explainability",
        "8. Outcomes",
        "9. Learning",
        "10. Safety Boundary",
    )

    explanation = (
        "The dashboard begins with revenue exposure.",
        "It identifies risk and high-priority customers.",
        "It forecasts expected collection.",
        "It compares scenarios before recommending an action.",
        "It explains the evidence behind the recommendation.",
        "It records governance and audit state.",
        "It waits for a real-world outcome before evaluating learning.",
        "No financial or provider action is automatically executed.",
    )

    headline = (
        "REVENEX turns fragmented revenue signals into an "
        "explainable, human-controlled decision workflow."
    )

    return DashboardProof(
        title="REVENEX Revenue Command Center",
        state="DEMO_READY",
        headline=headline,
        metrics=metrics,
        intelligence_sections=intelligence_sections,
        pipeline=pipeline,
        safety=safety,
        governance=governance,
        demo_sequence=demo_sequence,
        explanation=explanation,
    )
