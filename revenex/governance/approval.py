
"""
REVENEX Phase 16 — Human Approval & Governance.

All consequential decisions pass through explicit policy,
risk, and human-approval checks.

Execution remains disabled during development.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GovernanceDecision(str, Enum):
    ALLOW_REVIEW = "ALLOW_REVIEW"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class GovernancePolicy:
    execution_enabled: bool = False
    automatic_actions_enabled: bool = False
    financial_mutation_enabled: bool = False
    provider_mutation_enabled: bool = False
    human_approval_required: bool = True
    max_risk_without_approval: str = "LOW"


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    decision_id: str
    action: str
    confidence: float
    risk: str
    expected_impact: float
    status: ApprovalStatus
    requested_by: str
    reason: str


@dataclass(frozen=True)
class GovernanceEvaluation:
    decision_id: str
    governance_decision: GovernanceDecision
    approval_status: ApprovalStatus
    policy_passed: bool
    risk_check_passed: bool
    human_approval_required: bool
    execution_allowed: bool
    automatic_action_allowed: bool
    financial_mutation_allowed: bool
    provider_mutation_allowed: bool
    reasons: tuple[str, ...]


def _risk_level(value: str) -> int:
    return {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }.get(str(value).upper(), 4)


def evaluate_governance(
    *,
    decision_id: str,
    action: str,
    confidence: float,
    risk: str,
    expected_impact: float,
    policy: GovernancePolicy | None = None,
) -> GovernanceEvaluation:
    """
    Evaluate whether a decision may proceed.

    Development safety rule:
        execution is NEVER enabled by this function.
    """

    policy = policy or GovernancePolicy()

    reasons: list[str] = []

    confidence = max(
        0.0,
        min(1.0, float(confidence)),
    )

    risk = str(risk).upper()

    policy_passed = True
    risk_check_passed = True

    if not policy.execution_enabled:
        reasons.append(
            "Execution is disabled by governance policy."
        )

    if not policy.automatic_actions_enabled:
        reasons.append(
            "Automatic actions are disabled."
        )

    if not policy.financial_mutation_enabled:
        reasons.append(
            "Financial mutation is disabled."
        )

    if not policy.provider_mutation_enabled:
        reasons.append(
            "Provider mutation is disabled."
        )

    if _risk_level(risk) > _risk_level(
        policy.max_risk_without_approval
    ):
        risk_check_passed = False
        reasons.append(
            f"Risk {risk} exceeds the "
            f"no-approval threshold."
        )

    if confidence < 0.50:
        reasons.append(
            "Decision confidence is below 50%."
        )

    if expected_impact < 0:
        policy_passed = False
        reasons.append(
            "Expected impact cannot be negative."
        )

    human_required = (
        policy.human_approval_required
        or not policy.execution_enabled
        or not risk_check_passed
    )

    if not policy_passed:
        governance_decision = (
            GovernanceDecision.BLOCK
        )
        approval_status = ApprovalStatus.REJECTED

    elif human_required:
        governance_decision = (
            GovernanceDecision.REQUIRE_HUMAN_APPROVAL
        )
        approval_status = ApprovalStatus.PENDING

    else:
        governance_decision = (
            GovernanceDecision.ALLOW_REVIEW
        )
        approval_status = ApprovalStatus.NOT_REQUIRED

    return GovernanceEvaluation(
        decision_id=decision_id,
        governance_decision=governance_decision,
        approval_status=approval_status,
        policy_passed=policy_passed,
        risk_check_passed=risk_check_passed,
        human_approval_required=human_required,
        execution_allowed=False,
        automatic_action_allowed=False,
        financial_mutation_allowed=False,
        provider_mutation_allowed=False,
        reasons=tuple(reasons),
    )


def create_approval_request(
    *,
    approval_id: str,
    decision_id: str,
    action: str,
    confidence: float,
    risk: str,
    expected_impact: float,
    requested_by: str = "REVENEX",
    reason: str = "Human approval required.",
) -> ApprovalRequest:
    """
    Create a pending approval request.

    Creating an approval request does not execute anything.
    """

    return ApprovalRequest(
        approval_id=str(approval_id),
        decision_id=str(decision_id),
        action=str(action),
        confidence=max(
            0.0,
            min(1.0, float(confidence)),
        ),
        risk=str(risk).upper(),
        expected_impact=max(
            0.0,
            float(expected_impact),
        ),
        status=ApprovalStatus.PENDING,
        requested_by=str(requested_by),
        reason=str(reason),
    )


def approve_request(
    request: ApprovalRequest,
    *,
    approver: str,
) -> ApprovalRequest:
    """
    Record human approval.

    IMPORTANT:
        Approval itself still does not execute financial
        or provider actions.
    """

    if not str(approver).strip():
        raise ValueError(
            "Approver identity is required."
        )

    return ApprovalRequest(
        approval_id=request.approval_id,
        decision_id=request.decision_id,
        action=request.action,
        confidence=request.confidence,
        risk=request.risk,
        expected_impact=request.expected_impact,
        status=ApprovalStatus.APPROVED,
        requested_by=request.requested_by,
        reason=(
            f"Approved by {approver}."
        ),
    )


def reject_request(
    request: ApprovalRequest,
    *,
    approver: str,
    reason: str = "Rejected by human reviewer.",
) -> ApprovalRequest:
    """
    Record human rejection.
    """

    if not str(approver).strip():
        raise ValueError(
            "Approver identity is required."
        )

    return ApprovalRequest(
        approval_id=request.approval_id,
        decision_id=request.decision_id,
        action=request.action,
        confidence=request.confidence,
        risk=request.risk,
        expected_impact=request.expected_impact,
        status=ApprovalStatus.REJECTED,
        requested_by=request.requested_by,
        reason=str(reason),
    )


def approval_to_dict(
    request: ApprovalRequest,
) -> dict[str, Any]:
    return asdict(request)


def governance_to_dict(
    evaluation: GovernanceEvaluation,
) -> dict[str, Any]:
    payload = asdict(evaluation)
    payload["governance_decision"] = (
        evaluation.governance_decision.value
    )
    payload["approval_status"] = (
        evaluation.approval_status.value
    )
    payload["reasons"] = list(
        evaluation.reasons
    )
    return payload
