from revenex.phase17 import (
    ScenarioType,
    run_strategic_scenarios,
)


def test_all_strategic_scenarios_are_generated():
    report = run_strategic_scenarios(
        current_exposure=550000,
        baseline_collection=121500,
    )

    assert len(report.scenarios) == 5

    assert {
        scenario.scenario
        for scenario in report.scenarios
    } == {
        ScenarioType.BASELINE,
        ScenarioType.CONSERVATIVE,
        ScenarioType.BALANCED,
        ScenarioType.AGGRESSIVE,
        ScenarioType.STRESS,
    }


def test_aggressive_scenario_matches_planning_model():
    report = run_strategic_scenarios(
        current_exposure=550000,
        baseline_collection=121500,
    )

    aggressive = next(
        item
        for item in report.scenarios
        if item.scenario == ScenarioType.AGGRESSIVE
    )

    assert aggressive.expected_collection == 484000
    assert aggressive.remaining_exposure == 66000
    assert aggressive.recovery_rate == 0.88
    assert aggressive.incremental_collection == 362500
    assert aggressive.confidence == 0.62


def test_stress_scenario_is_lower_than_aggressive():
    report = run_strategic_scenarios(
        current_exposure=550000,
        baseline_collection=121500,
    )

    aggressive = next(
        item
        for item in report.scenarios
        if item.scenario == ScenarioType.AGGRESSIVE
    )

    stress = next(
        item
        for item in report.scenarios
        if item.scenario == ScenarioType.STRESS
    )

    assert stress.expected_collection < aggressive.expected_collection
    assert stress.remaining_exposure > aggressive.remaining_exposure


def test_selected_scenario_is_preserved():
    report = run_strategic_scenarios(
        current_exposure=550000,
        baseline_collection=121500,
        selected_scenario=ScenarioType.BALANCED,
    )

    assert report.selected_scenario == ScenarioType.BALANCED


def test_scenario_spread_is_deterministic():
    report = run_strategic_scenarios(
        current_exposure=550000,
        baseline_collection=121500,
    )

    assert report.scenario_spread == 319000


def test_evidence_is_present():
    report = run_strategic_scenarios(
        current_exposure=100000,
        baseline_collection=45000,
    )

    for scenario in report.scenarios:
        assert len(scenario.evidence_refs) == 4
        assert scenario.read_only is True
        assert scenario.human_review_required is True
        assert scenario.interpretation


def test_governance_is_locked():
    report = run_strategic_scenarios(
        current_exposure=100000,
        baseline_collection=45000,
    )

    assert report.read_only is True
    assert report.human_review_required is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False


def test_zero_exposure_is_safe():
    report = run_strategic_scenarios(
        current_exposure=0,
        baseline_collection=50000,
    )

    assert report.current_exposure == 0
    assert report.baseline_collection == 0
    assert report.best_expected_collection == 0
    assert report.scenario_spread == 0

    for scenario in report.scenarios:
        assert scenario.expected_collection == 0
        assert scenario.remaining_exposure == 0


def test_planning_is_deterministic():
    kwargs = {
        "current_exposure": 550000,
        "baseline_collection": 121500,
        "selected_scenario": ScenarioType.AGGRESSIVE,
    }

    first = run_strategic_scenarios(**kwargs)
    second = run_strategic_scenarios(**kwargs)

    assert first == second
