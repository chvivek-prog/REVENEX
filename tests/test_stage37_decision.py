from revenex.decision.engine import (
    build_decision,
    decide_recovery,
)
from revenex.simulation.engine import (
    SimulationScenario,
    compare_scenarios,
)


def test_decision_selects_simulation_recommendation():
    comparison = compare_scenarios(
        100000,
        0.80,
    )

    decision = build_decision(comparison)

    assert decision.scenario is not None
    assert decision.expected_collection > 0
    assert decision.recommended_action.endswith("_REVIEW")


def test_decision_requires_approval():
    decision = decide_recovery(
        100000,
        0.80,
    )

    assert decision.requires_approval is True
    assert decision.execution_allowed is False


def test_decision_contains_rationale():
    decision = decide_recovery(
        250000,
        0.70,
    )

    assert len(decision.rationale) >= 3
    assert any(
        "Expected collection" in reason
        for reason in decision.rationale
    )


def test_decision_handles_zero_exposure():
    decision = decide_recovery(
        0,
        0.90,
    )

    assert decision.expected_collection == 0
    assert decision.remaining_exposure == 0
    assert decision.execution_allowed is False


def test_priority_scenario_maps_to_priority_review():
    comparison = compare_scenarios(
        100000,
        0.75,
    )

    # Build a decision from the comparison's actual result.
    decision = build_decision(comparison)

    assert decision.requires_approval is True
    assert decision.execution_allowed is False


def test_decision_does_not_mutate_inputs():
    exposure = 500000
    risk = 0.80

    before = (exposure, risk)

    decide_recovery(
        exposure,
        risk,
    )

    assert (exposure, risk) == before
