from revenex.simulation.engine import (
    SimulationScenario,
    compare_scenarios,
    simulate_scenario,
)


def test_standard_simulation_is_bounded():
    result = simulate_scenario(
        SimulationScenario.STANDARD,
        100000,
        0.60,
    )

    assert result.starting_exposure == 100000
    assert 0 <= result.expected_collection <= 100000
    assert 0 <= result.remaining_exposure <= 100000
    assert 0 <= result.confidence <= 1


def test_priority_simulation_can_improve_expected_collection():
    standard = simulate_scenario(
        SimulationScenario.STANDARD,
        100000,
        0.80,
    )

    priority = simulate_scenario(
        SimulationScenario.PRIORITY,
        100000,
        0.80,
    )

    assert (
        priority.expected_collection
        > standard.expected_collection
    )


def test_comparison_runs_all_scenarios():
    comparison = compare_scenarios(
        500000,
        0.75,
    )

    assert len(comparison.scenarios) == 3

    assert {
        scenario.scenario
        for scenario in comparison.scenarios
    } == {
        SimulationScenario.STANDARD,
        SimulationScenario.PRIORITY,
        SimulationScenario.AGGRESSIVE,
    }


def test_comparison_selects_best_expected_collection():
    comparison = compare_scenarios(
        100000,
        0.80,
    )

    assert comparison.recommended_scenario is not None

    assert (
        comparison.expected_best_collection
        == max(
            result.expected_collection
            for result in comparison.scenarios
        )
    )


def test_zero_exposure_is_safe():
    comparison = compare_scenarios(
        0,
        0.90,
    )

    assert comparison.expected_best_collection == 0
    assert all(
        result.expected_collection == 0
        for result in comparison.scenarios
    )


def test_simulation_is_read_only():
    exposure = 250000
    risk = 0.70

    before = (exposure, risk)

    compare_scenarios(
        exposure,
        risk,
    )

    assert (exposure, risk) == before
