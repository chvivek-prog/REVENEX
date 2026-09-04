
from revenex.os.architecture import (
    RevenueOSStage,
    RevenueOSState,
    build_revenue_os,
    revenue_os_to_dict,
)


def test_final_pipeline_contains_all_os_stages():

    os_state = build_revenue_os(
        "phase20-test"
    )

    assert os_state.pipeline == (
        "OBSERVE",
        "UNDERSTAND",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "HUMAN_APPROVAL",
        "SAFELY_ACT",
        "MONITOR",
        "OUTCOME",
        "LEARN",
        "AUDIT",
    )


def test_os_starts_in_intelligence_mode():

    os_state = build_revenue_os(
        "decision-1"
    )

    assert (
        os_state.current_stage
        == RevenueOSStage.OBSERVE
    )

    assert (
        os_state.state
        == RevenueOSState.INTELLIGENCE
    )


def test_human_approval_is_permanent_boundary():

    os_state = build_revenue_os(
        "decision-2",
        stage=RevenueOSStage.HUMAN_APPROVAL,
    )

    assert (
        os_state.state
        == RevenueOSState.AWAITING_APPROVAL
    )

    assert os_state.human_approval_required is True
    assert os_state.automatic_action is False
    assert os_state.execution_allowed is False


def test_safe_action_is_not_automatic():

    os_state = build_revenue_os(
        "decision-3",
        stage=RevenueOSStage.SAFELY_ACT,
    )

    assert (
        os_state.state
        == RevenueOSState.EXECUTING
    )

    assert os_state.execution_allowed is False
    assert os_state.automatic_action is False
    assert os_state.financial_mutation is False
    assert os_state.provider_mutation is False


def test_learning_requires_real_outcome():

    os_state = build_revenue_os(
        "decision-4",
        stage=RevenueOSStage.LEARN,
    )

    assert (
        os_state.state
        == RevenueOSState.LEARNING
    )

    assert (
        os_state.outcome_required_for_learning
        is True
    )

    assert (
        os_state.model_mutation_allowed
        is False
    )


def test_audit_is_terminal_governance_state():

    os_state = build_revenue_os(
        "decision-5",
        stage=RevenueOSStage.AUDIT,
    )

    assert (
        os_state.state
        == RevenueOSState.AUDITED
    )

    assert os_state.is_governed is True


def test_governance_flags_are_safe():

    os_state = build_revenue_os(
        "safety-test"
    )

    assert os_state.execution_allowed is False
    assert os_state.automatic_action is False
    assert os_state.financial_mutation is False
    assert os_state.provider_mutation is False
    assert os_state.model_mutation_allowed is False
    assert os_state.human_approval_required is True


def test_serialization_exposes_governance():

    os_state = build_revenue_os(
        "serialization-test"
    )

    payload = revenue_os_to_dict(
        os_state
    )

    assert payload["decision_id"] == (
        "serialization-test"
    )

    assert payload["current_stage"] == "OBSERVE"
    assert payload["state"] == "INTELLIGENCE"
    assert payload["governed"] is True
    assert payload["execution_allowed"] is False
