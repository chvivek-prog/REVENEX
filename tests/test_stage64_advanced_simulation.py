
from revenex.simulation.advanced import (
    SimulationScenario,
    SimulationRisk,
    simulate_revenue,
    simulate_scenarios,
)


def test_all_standard_scenarios_exist():
    results = simulate_scenarios(550000)

    assert len(results) == 4

    assert [
        result.scenario
        for result in results
    ] == [
        SimulationScenario.CONSERVATIVE,
        SimulationScenario.BALANCED,
        SimulationScenario.AGGRESSIVE,
        SimulationScenario.CUSTOM,
    ]


def test_aggressive_matches_current_recovery_baseline():
    result = simulate_revenue(
        550000,
        scenario=SimulationScenario.AGGRESSIVE,
    )

    assert result.expected_collection == 483120.0
    assert result.remaining_exposure == 66880.0
    assert result.confidence == 0.62
    assert result.risk == SimulationRisk.HIGH


def test_scenarios_are_deterministic():
    first = simulate_scenarios(550000)
    second = simulate_scenarios(550000)

    assert first == second


def test_expected_collection_is_bounded():
    for result in simulate_scenarios(550000):

        assert (
            0
            <= result.expected_collection
            <= 550000
        )

        assert (
            0
            <= result.remaining_exposure
            <= 550000
        )


def test_custom_scenario():
    result = simulate_revenue(
        550000,
        scenario=SimulationScenario.CUSTOM,
        custom={
            "collection_rate": 0.90,
            "confidence": 0.81,
            "risk": "MEDIUM",
            "recovery_strategy": "CUSTOM_RECOVERY",
            "discount_strategy": "NO_DISCOUNT",
        },
    )

    assert result.scenario == SimulationScenario.CUSTOM
    assert result.expected_collection == 495000.0
    assert result.remaining_exposure == 55000.0
    assert result.confidence == 0.81


def test_simulation_is_read_only():
    result = simulate_revenue(
        550000,
        scenario="BALANCED",
    )

    assert result.read_only is True
    assert result.financial_mutation is False
    assert result.provider_mutation is False
    assert result.execution_allowed is False
    assert result.automatic_action is False
    assert result.human_approval_required is True


def test_strategy_dimensions_are_present():
    result = simulate_revenue(
        550000,
        scenario="AGGRESSIVE",
    )

    assert result.recovery_strategy
    assert result.pricing_strategy
    assert result.discount_strategy
    assert result.payment_retry_strategy
    assert result.collection_timing
    assert result.cash_management


def test_zero_portfolio():
    results = simulate_scenarios(0)

    for result in results:
        assert result.expected_collection == 0.0
        assert result.remaining_exposure == 0.0


def test_negative_portfolio_is_safe():
    results = simulate_scenarios(-100000)

    for result in results:
        assert result.expected_collection == 0.0
        assert result.remaining_exposure == 0.0
