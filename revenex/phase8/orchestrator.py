from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from revenex.phase5 import analyze_opportunities
from revenex.phase6 import build_action_plans
from revenex.phase7 import build_decision_trace


@dataclass(frozen=True)
class IntelligencePipeline:
    opportunities: Any
    action_plans: Any
    decision_trace: Any


@dataclass(frozen=True)
class PipelineResult:
    pipeline: IntelligencePipeline
    status: str
    total_opportunities: int
    total_action_plans: int
    total_decisions: int
    highest_priority: str
    governance_state: str

    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _opportunity_inputs(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized = []

    for item in items:
        normalized.append(
            {
                "opportunity_id": (
                    item.get("opportunity_id")
                    or item.get("resource_id")
                    or item.get("id")
                ),
                "category": item.get("category") or item.get("type"),
                "exposure": (
                    item.get("exposure")
                    or item.get("revenue_at_risk")
                    or item.get("outstanding")
                ),
                "recoverable_value": (
                    item.get("recoverable_value")
                    or item.get("expected_recovery")
                    or item.get("expected_collection")
                ),
                "probability": item.get("probability", 0.0),
                "urgency": item.get("urgency", 0.0),
                "confidence": item.get("confidence", 0.0),
                "evidence_quality": item.get("evidence_quality", 0.0),
            }
        )

    return normalized


def _plan_inputs(opportunities: Any) -> list[dict[str, Any]]:
    return [
        {
            "opportunity_id": opportunity.opportunity_id,
            "priority": opportunity.priority,
            "recoverable_value": opportunity.recoverable_value,
            "confidence": opportunity.confidence,
            "category": opportunity.category,
        }
        for opportunity in opportunities
    ]


def _decision_inputs(
    plans: Any,
    opportunities: Any,
) -> list[dict[str, Any]]:
    opportunity_map = {
        opportunity.opportunity_id: opportunity
        for opportunity in opportunities
    }

    decisions = []

    for plan in plans:
        opportunity = opportunity_map.get(plan.opportunity_id)

        evidence = [
            f"priority={plan.priority}",
            f"expected_value={plan.expected_value:.2f}",
            f"confidence={plan.confidence:.4f}",
        ]

        if opportunity is not None:
            evidence.append(
                f"evidence_quality={opportunity.evidence_quality:.4f}"
            )

        decisions.append(
            {
                "decision_id": plan.plan_id,
                "decision": plan.action_type,
                "scenario": plan.priority,
                "confidence": plan.confidence,
                "expected_value": plan.expected_value,
                "remaining_exposure": (
                    opportunity.exposure
                    if opportunity is not None
                    else 0.0
                ),
                "evidence": evidence,
                "risks": [
                    f"urgency={plan.urgency}",
                ],
                "alternatives": [
                    "HUMAN_REVIEW",
                    "DEFER",
                ],
            }
        )

    return decisions


def run_intelligence_pipeline(
    items: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> PipelineResult:
    source_items = list(items)

    opportunity_report = analyze_opportunities(
        _opportunity_inputs(source_items)
    )

    action_plan_report = build_action_plans(
        _plan_inputs(opportunity_report.opportunities)
    )

    decision_report = build_decision_trace(
        _decision_inputs(
            action_plan_report.plans,
            opportunity_report.opportunities,
        )
    )

    pipeline = IntelligencePipeline(
        opportunities=opportunity_report,
        action_plans=action_plan_report,
        decision_trace=decision_report,
    )

    return PipelineResult(
        pipeline=pipeline,
        status="COMPLETE",
        total_opportunities=(
            opportunity_report.total_opportunities
        ),
        total_action_plans=(
            action_plan_report.total_plans
        ),
        total_decisions=(
            decision_report.total_decisions
        ),
        highest_priority=(
            opportunity_report.highest_priority
        ),
        governance_state=(
            decision_report.governance_state
        ),
    )
