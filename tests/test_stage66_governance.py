
from revenex.governance.approval import (
    ApprovalStatus,
    GovernanceDecision,
    approve_request,
    create_approval_request,
    evaluate_governance,
    reject_request,
)


def test_high_risk_requires_human_approval():

    result = evaluate_governance(
        decision_id="stage66-high",
        action="AGGRESSIVE_RECOVERY_REVIEW",
        confidence=0.62,
        risk="HIGH",
        expected_impact=483120,
    )

    assert (
        result.governance_decision
        == GovernanceDecision.REQUIRE_HUMAN_APPROVAL
    )

    assert (
        result.approval_status
        == ApprovalStatus.PENDING
    )

    assert result.human_approval_required is True


def test_execution_remains_disabled():

    result = evaluate_governance(
        decision_id="safety",
        action="BALANCED_RECOVERY_REVIEW",
        confidence=0.90,
        risk="LOW",
        expected_impact=400000,
    )

    assert result.execution_allowed is False
    assert result.automatic_action_allowed is False
    assert result.financial_mutation_allowed is False
    assert result.provider_mutation_allowed is False


def test_create_approval_request():

    request = create_approval_request(
        approval_id="approval-1",
        decision_id="decision-1",
        action="AGGRESSIVE_RECOVERY_REVIEW",
        confidence=0.62,
        risk="HIGH",
        expected_impact=483120,
    )

    assert request.status == ApprovalStatus.PENDING
    assert request.decision_id == "decision-1"
    assert request.expected_impact == 483120


def test_human_can_approve():

    request = create_approval_request(
        approval_id="approval-2",
        decision_id="decision-2",
        action="BALANCED_RECOVERY_REVIEW",
        confidence=0.80,
        risk="MEDIUM",
        expected_impact=450000,
    )

    approved = approve_request(
        request,
        approver="human-reviewer",
    )

    assert (
        approved.status
        == ApprovalStatus.APPROVED
    )

    assert (
        "human-reviewer"
        in approved.reason
    )


def test_human_can_reject():

    request = create_approval_request(
        approval_id="approval-3",
        decision_id="decision-3",
        action="AGGRESSIVE_RECOVERY_REVIEW",
        confidence=0.60,
        risk="HIGH",
        expected_impact=483120,
    )

    rejected = reject_request(
        request,
        approver="human-reviewer",
        reason="Risk too high.",
    )

    assert (
        rejected.status
        == ApprovalStatus.REJECTED
    )

    assert rejected.reason == "Risk too high."


def test_approval_does_not_enable_execution():

    governance = evaluate_governance(
        decision_id="decision-4",
        action="AGGRESSIVE_RECOVERY_REVIEW",
        confidence=0.95,
        risk="LOW",
        expected_impact=500000,
    )

    request = create_approval_request(
        approval_id="approval-4",
        decision_id="decision-4",
        action="AGGRESSIVE_RECOVERY_REVIEW",
        confidence=0.95,
        risk="LOW",
        expected_impact=500000,
    )

    approved = approve_request(
        request,
        approver="authorized-human",
    )

    assert approved.status == ApprovalStatus.APPROVED

    # Approval state is not execution permission.
    assert governance.execution_allowed is False
    assert governance.financial_mutation_allowed is False
    assert governance.provider_mutation_allowed is False


def test_missing_approver_rejected():

    request = create_approval_request(
        approval_id="approval-5",
        decision_id="decision-5",
        action="TEST",
        confidence=0.80,
        risk="LOW",
        expected_impact=100,
    )

    try:
        approve_request(
            request,
            approver="",
        )
        assert False
    except ValueError:
        assert True
