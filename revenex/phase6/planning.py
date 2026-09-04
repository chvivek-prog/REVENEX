from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionPlan:
    plan_id: str
    opportunity_id: str
    action_type: str
    priority: str
    urgency: str
    expected_value: float
    confidence: float
    sequence: int
    rationale: str
    dependencies: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class ActionPlanReport:
    plans: tuple[ActionPlan, ...]
    total_plans: int
    total_expected_value: float
    highest_priority: str
    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _confidence(value: Any) -> float:
    try:
        return min(max(float(value or 0), 0.0), 1.0)
    except (TypeError, ValueError):
        return 0.0


def _priority_rank(priority: str) -> int:
    return {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }.get(priority.upper(), 0)


def _urgency(priority: str, confidence: float) -> str:
    rank = _priority_rank(priority)

    if rank >= 4 and confidence >= 0.70:
        return "IMMEDIATE"
    if rank >= 3:
        return "HIGH"
    if rank >= 2:
        return "NORMAL"
    return "LOW"


def _action_type(item: dict[str, Any]) -> str:
    explicit = item.get("recommended_action") or item.get("action_type")
    if explicit:
        return str(explicit)

    category = str(
        item.get("category")
        or item.get("type")
        or "REVENUE_RECOVERY"
    ).upper()

    if "SETTLEMENT" in category:
        return "SETTLEMENT_REVIEW"
    if "INVOICE" in category:
        return "INVOICE_RECOVERY_REVIEW"
    if "PAYOUT" in category:
        return "PAYOUT_REVIEW"
    if "ANOMAL" in category:
        return "ANOMALY_INVESTIGATION"

    return "REVENUE_RECOVERY_REVIEW"


def build_action_plans(
    opportunities: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> ActionPlanReport:
    plans: list[ActionPlan] = []

    normalized = []

    for index, item in enumerate(opportunities):
        opportunity_id = str(
            item.get("opportunity_id")
            or item.get("resource_id")
            or item.get("id")
            or f"opportunity-{index + 1}"
        )

        priority = str(
            item.get("priority")
            or "MEDIUM"
        ).upper()

        expected_value = _money(
            item.get("expected_value")
            or item.get("recoverable_value")
            or item.get("expected_recovery")
        )

        confidence = _confidence(item.get("confidence"))

        normalized.append(
            (
                opportunity_id,
                priority,
                expected_value,
                confidence,
                item,
            )
        )

    normalized.sort(
        key=lambda x: (
            _priority_rank(x[1]),
            x[2],
            x[3],
        ),
        reverse=True,
    )

    for sequence, (
        opportunity_id,
        priority,
        expected_value,
        confidence,
        item,
    ) in enumerate(normalized, start=1):

        urgency = _urgency(priority, confidence)
        action_type = _action_type(item)

        raw_dependencies = item.get("dependencies") or ()
        if isinstance(raw_dependencies, str):
            dependencies = (raw_dependencies,)
        else:
            dependencies = tuple(str(x) for x in raw_dependencies)

        rationale = (
            f"{action_type} recommended for {opportunity_id}. "
            f"Priority={priority}, urgency={urgency}, "
            f"expected value=₹{expected_value:,.2f}, "
            f"confidence={confidence:.0%}. "
            f"Human review is required before any action."
        )

        plans.append(
            ActionPlan(
                plan_id=f"plan-{sequence}-{opportunity_id}",
                opportunity_id=opportunity_id,
                action_type=action_type,
                priority=priority,
                urgency=urgency,
                expected_value=round(expected_value, 2),
                confidence=round(confidence, 4),
                sequence=sequence,
                rationale=rationale,
                dependencies=dependencies,
            )
        )

    highest_priority = (
        plans[0].priority
        if plans
        else "NONE"
    )

    return ActionPlanReport(
        plans=tuple(plans),
        total_plans=len(plans),
        total_expected_value=round(
            sum(plan.expected_value for plan in plans),
            2,
        ),
        highest_priority=highest_priority,
    )
