from revenex.phase1 import (
    get_demo_scenario,
    get_demo_scenarios,
)


def test_demo_scenarios_exist():
    scenarios = get_demo_scenarios()

    assert len(scenarios) >= 4
    assert {
        "healthy",
        "collection_risk",
        "settlement_variance",
        "recovery_opportunity",
    }.issubset(
        {item.scenario_id for item in scenarios}
    )


def test_collection_risk_scenario():
    scenario = get_demo_scenario("collection_risk")

    assert scenario is not None
    assert scenario.data["invoice_amount"] == 550000
    assert scenario.data["collected_amount"] == 121500


def test_unknown_scenario_is_safe():
    assert get_demo_scenario("does-not-exist") is None
