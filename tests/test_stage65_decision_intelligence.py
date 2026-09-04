
from revenex.decision.intelligence import (
    build_decision,
    decision_to_dict,
)

from revenex.simulation.advanced import (
    SimulationScenario,
    simulate_scenarios,
)


def test_decision_selects_best_simulated_collection():

    simulations = simulate_scenarios(
        550000
    )

    decision = build_decision(
        simulations,
        decision_id="stage65",
    )

    assert (
        decision.recommended_action
        == "AGGRESSIVE_RECOVERY_REVIEW"
    )

    assert (
        decision.expected_impact
        == 483120.0
    )

    assert decision.confidence == 0.62
    assert decision.risk == "HIGH"


def test_decision_contains_alternatives():

    decision = build_decision(
        simulate_scenarios(550000),
        decision_id="alternatives",
    )

    assert len(
        decision.alternatives
    ) == 3

    scenarios = {
        item.scenario
        for item in decision.alternatives
    }

    assert (
        SimulationScenario.CONSERVATIVE.value
        in scenarios
    )

    assert (
        SimulationScenario.BALANCED.value
        in scenarios
    )

    assert (
        SimulationScenario.CUSTOM.value
        in scenarios
    )


def test_decision_contains_explanation():

    decision = build_decision(
        simulate_scenarios(550000),
        decision_id="explain",
    )

    assert decision.why
    assert "AGGRESSIVE" in decision.why
    assert "₹483,120.00" in decision.why
    assert "human approval" in (
        decision.why.lower()
    )


def test_decision_contains_evidence():

    decision = build_decision(
        simulate_scenarios(550000),
        decision_id="evidence",
    )

    assert decision.evidence

    assert any(
        "expected_collection=483120.00"
        in item
        for item in decision.evidence
    )


def test_decision_governance():

    decision = build_decision(
        simulate_scenarios(550000)
    )

    assert decision.read_only is True
    assert decision.approval_required is True
    assert decision.human_approval_required is True

    assert decision.execution_allowed is False
    assert decision.automatic_action is False
    assert decision.financial_mutation is False
    assert decision.provider_mutation is False


def test_empty_simulation_requires_review():

    decision = build_decision(
        (),
        decision_id="empty",
    )

    assert (
        decision.recommended_action
        == "MONITOR"
    )

    assert decision.confidence == 0.0
    assert decision.expected_impact == 0.0
    assert decision.approval_required is True


def test_decision_serialization():

    decision = build_decision(
        simulate_scenarios(550000),
        decision_id="serialize",
    )

    payload = decision_to_dict(
        decision
    )

    assert (
        payload["decision_id"]
        == "serialize"
    )

    assert (
        payload["recommended_action"]
        == "AGGRESSIVE_RECOVERY_REVIEW"
    )

    assert (
        payload["expected_impact"]
        == 483120.0
    )

    assert (
        payload["approval_required"]
        is True
    )

    assert (
        payload["governance"]
        ["financial_mutation"]
        is False
    )
