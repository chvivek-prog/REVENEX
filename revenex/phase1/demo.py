from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DemoScenario:
    scenario_id: str
    name: str
    description: str
    data: dict[str, Any]


_SCENARIOS = (
    DemoScenario(
        scenario_id="healthy",
        name="Healthy Revenue",
        description="Normal collection and settlement flow.",
        data={
            "invoice_amount": 500000,
            "collected_amount": 480000,
            "settled_amount": 478000,
            "fees": 3000,
            "tax": 1000,
        },
    ),
    DemoScenario(
        scenario_id="collection_risk",
        name="Collection Risk",
        description="Large overdue exposure requiring recovery review.",
        data={
            "invoice_amount": 550000,
            "collected_amount": 121500,
            "settled_amount": 120000,
            "fees": 3000,
            "tax": 1000,
        },
    ),
    DemoScenario(
        scenario_id="settlement_variance",
        name="Settlement Variance",
        description="Settlement does not match the expected money flow.",
        data={
            "invoice_amount": 400000,
            "collected_amount": 400000,
            "settled_amount": 375000,
            "fees": 5000,
            "tax": 2000,
        },
    ),
    DemoScenario(
        scenario_id="recovery_opportunity",
        name="Recovery Opportunity",
        description="High-risk exposure with meaningful recoverable value.",
        data={
            "invoice_amount": 750000,
            "collected_amount": 250000,
            "settled_amount": 245000,
            "fees": 4000,
            "tax": 1000,
        },
    ),
)


def get_demo_scenarios() -> tuple[DemoScenario, ...]:
    return _SCENARIOS


def get_demo_scenario(
    scenario_id: str,
) -> DemoScenario | None:
    for scenario in _SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None
