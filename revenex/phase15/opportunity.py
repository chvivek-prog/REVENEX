from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class OpportunityPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class RevenueOpportunity:
    opportunity_id: str
    customer_id: str
    exposure: float
    recoverable_amount: float
    opportunity_score: float
    priority: OpportunityPriority
    reason: str
    evidence_refs: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True


@dataclass(frozen=True)
class OpportunityReport:
    opportunities: tuple[RevenueOpportunity, ...]
    total_opportunity: float
    critical_opportunities: int
    high_opportunities: int
    average_score: float
    highest_priority_customer: str | None
    summary: str

    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _number(value: Any) -> float:
    try:
        return max(float(value or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _priority(score: float) -> OpportunityPriority:
    if score >= 0.85:
        return OpportunityPriority.CRITICAL
    if score >= 0.65:
        return OpportunityPriority.HIGH
    if score >= 0.40:
        return OpportunityPriority.MEDIUM
    return OpportunityPriority.LOW


def identify_revenue_opportunities(
    customers: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> OpportunityReport:

    opportunities: list[RevenueOpportunity] = []

    for index, customer in enumerate(customers, start=1):
        customer_id = str(
            customer.get("customer_id")
            or customer.get("id")
            or f"customer-{index}"
        )

        exposure = _number(
            customer.get("exposure")
            or customer.get("outstanding")
            or customer.get("amount")
        )

        risk = _number(customer.get("risk_score"))
        confidence = _number(customer.get("confidence"))

        recoverable = _number(
            customer.get("recoverable_amount")
        )

        if recoverable == 0:
            recovery_rate = _number(
                customer.get("recovery_rate")
            )
            recoverable = exposure * recovery_rate

        if exposure <= 0:
            continue

        # Opportunity score deliberately remains deterministic.
        score = round(
            min(
                1.0,
                (exposure / max(exposure, 1.0)) * 0.45
                + risk * 0.35
                + confidence * 0.20,
            ),
            4,
        )

        priority = _priority(score)

        if recoverable <= 0:
            recoverable = round(
                exposure * min(max(score, 0.0), 1.0),
                2,
            )

        reason_parts = []

        if risk >= 0.70:
            reason_parts.append("elevated revenue risk")

        if confidence >= 0.70:
            reason_parts.append("strong evidence confidence")

        if not reason_parts:
            reason_parts.append(
                "recoverable revenue exposure identified"
            )

        opportunities.append(
            RevenueOpportunity(
                opportunity_id=f"OPP-{index:04d}",
                customer_id=customer_id,
                exposure=round(exposure, 2),
                recoverable_amount=round(recoverable, 2),
                opportunity_score=score,
                priority=priority,
                reason="; ".join(reason_parts),
                evidence_refs=(
                    f"customer:{customer_id}",
                    "risk_score",
                    "confidence",
                    "exposure",
                ),
            )
        )

    opportunities.sort(
        key=lambda item: (
            -item.opportunity_score,
            -item.recoverable_amount,
            item.customer_id,
        )
    )

    total_opportunity = round(
        sum(
            item.recoverable_amount
            for item in opportunities
        ),
        2,
    )

    critical_count = sum(
        item.priority == OpportunityPriority.CRITICAL
        for item in opportunities
    )

    high_count = sum(
        item.priority == OpportunityPriority.HIGH
        for item in opportunities
    )

    average_score = round(
        (
            sum(item.opportunity_score for item in opportunities)
            / len(opportunities)
        )
        if opportunities
        else 0.0,
        4,
    )

    highest_customer = (
        opportunities[0].customer_id
        if opportunities
        else None
    )

    summary = (
        f"{len(opportunities)} revenue opportunity(s) identified "
        f"with ₹{total_opportunity:,.2f} of estimated recoverable "
        f"revenue. Human review is required."
    )

    return OpportunityReport(
        opportunities=tuple(opportunities),
        total_opportunity=total_opportunity,
        critical_opportunities=critical_count,
        high_opportunities=high_count,
        average_score=average_score,
        highest_priority_customer=highest_customer,
        summary=summary,
    )
