"""
REVENEX Stage 36 — Simulation Engine.

Runs read-only recovery scenarios against the current revenue-risk
state. No financial, provider, customer, invoice, or payment state
is mutated.
"""

from dataclasses import dataclass
from enum import Enum


class SimulationScenario(str, Enum):
    STANDARD = "STANDARD"
    PRIORITY = "PRIORITY"
    AGGRESSIVE = "AGGRESSIVE"


@dataclass(frozen=True)
class SimulationResult:
    scenario: SimulationScenario
    starting_exposure: float
    expected_collection: float
    remaining_exposure: float
    revenue_at_risk_reduction: float
    confidence: float
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class SimulationComparison:
    scenarios: tuple[SimulationResult, ...]
    recommended_scenario: SimulationScenario | None
    expected_best_collection: float
    confidence: float


SCENARIO_FACTORS = {
    SimulationScenario.STANDARD: (0.60, 0.70),
    SimulationScenario.PRIORITY: (0.72, 0.78),
    SimulationScenario.AGGRESSIVE: (0.82, 0.62),
}


def simulate_scenario(
    scenario: SimulationScenario,
    starting_exposure: float,
    risk_score: float,
) -> SimulationResult:
    """
    Simulate a recovery scenario.

    risk_score is expected to be between 0 and 1.
    """

    exposure = max(0.0, float(starting_exposure))
    risk = max(0.0, min(1.0, float(risk_score)))

    base_factor, base_confidence = SCENARIO_FACTORS[scenario]

    # Higher risk creates more potential upside from intervention,
    # while the result remains bounded by the starting exposure.
    risk_adjustment = {
        SimulationScenario.STANDARD: 0.0,
        SimulationScenario.PRIORITY: risk * 0.05,
        SimulationScenario.AGGRESSIVE: risk * 0.08,
    }[scenario]

    collection_factor = min(
        1.0,
        base_factor + risk_adjustment,
    )

    expected_collection = exposure * collection_factor

    remaining_exposure = max(
        0.0,
        exposure - expected_collection,
    )

    revenue_at_risk_reduction = (
        expected_collection
    )

    confidence = max(
        0.0,
        min(
            1.0,
            base_confidence
            - (0.10 if risk > 0.85 and scenario == SimulationScenario.AGGRESSIVE else 0.0),
        ),
    )

    assumptions = (
        f"starting_exposure={exposure:.2f}",
        f"risk_score={risk:.4f}",
        f"collection_factor={collection_factor:.4f}",
        "simulation is advisory and does not execute recovery",
    )

    return SimulationResult(
        scenario=scenario,
        starting_exposure=exposure,
        expected_collection=expected_collection,
        remaining_exposure=remaining_exposure,
        revenue_at_risk_reduction=revenue_at_risk_reduction,
        confidence=confidence,
        assumptions=assumptions,
    )


def compare_scenarios(
    starting_exposure: float,
    risk_score: float,
) -> SimulationComparison:
    """Run every supported scenario and select the best expected result."""

    scenarios = tuple(
        simulate_scenario(
            scenario,
            starting_exposure,
            risk_score,
        )
        for scenario in SimulationScenario
    )

    best = max(
        scenarios,
        key=lambda result: (
            result.expected_collection,
            result.confidence,
        ),
        default=None,
    )

    return SimulationComparison(
        scenarios=scenarios,
        recommended_scenario=(
            best.scenario
            if best is not None
            else None
        ),
        expected_best_collection=(
            best.expected_collection
            if best is not None
            else 0.0
        ),
        confidence=(
            best.confidence
            if best is not None
            else 0.0
        ),
    )
