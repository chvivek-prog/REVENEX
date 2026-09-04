"""
REVENEX Stage 37 — Decision Intelligence.

Converts simulation results into a transparent advisory decision.

This layer NEVER executes the recommendation.
Every recommendation requires approval.
"""

from dataclasses import dataclass

from revenex.simulation.engine import (
    SimulationComparison,
    SimulationResult,
    SimulationScenario,
    compare_scenarios,
)


@dataclass(frozen=True)
class DecisionRecommendation:
    scenario: SimulationScenario | None
    recommended_action: str
    expected_collection: float
    remaining_exposure: float
    confidence: float
    rationale: tuple[str, ...]
    requires_approval: bool
    execution_allowed: bool


def _action_for_scenario(
    scenario: SimulationScenario | None,
) -> str:
    if scenario == SimulationScenario.AGGRESSIVE:
        return "AGGRESSIVE_RECOVERY_REVIEW"

    if scenario == SimulationScenario.PRIORITY:
        return "PRIORITY_RECOVERY_REVIEW"

    if scenario == SimulationScenario.STANDARD:
        return "STANDARD_RECOVERY_REVIEW"

    return "MONITOR"


def _select_result(
    comparison: SimulationComparison,
) -> SimulationResult | None:
    if comparison.recommended_scenario is None:
        return None

    for result in comparison.scenarios:
        if result.scenario == comparison.recommended_scenario:
            return result

    return None


def build_decision(
    comparison: SimulationComparison,
) -> DecisionRecommendation:
    """Create a transparent, approval-gated recommendation."""

    selected = _select_result(comparison)

    if selected is None or selected.starting_exposure <= 0:
        return DecisionRecommendation(
            scenario=None,
            recommended_action="MONITOR",
            expected_collection=0.0,
            remaining_exposure=0.0,
            confidence=0.0,
            rationale=(
                "No recoverable revenue exposure is present.",
                "Monitoring is recommended instead of recovery.",
            ),
            requires_approval=True,
            execution_allowed=False,
        )

    rationale = (
        f"Selected {selected.scenario.value} scenario.",
        f"Expected collection: ₹{selected.expected_collection:,.2f}.",
        f"Remaining exposure: ₹{selected.remaining_exposure:,.2f}.",
        f"Simulation confidence: {selected.confidence:.2%}.",
        "Recommendation is based on read-only scenario simulation.",
    )

    return DecisionRecommendation(
        scenario=selected.scenario,
        recommended_action=_action_for_scenario(
            selected.scenario
        ),
        expected_collection=selected.expected_collection,
        remaining_exposure=selected.remaining_exposure,
        confidence=selected.confidence,
        rationale=rationale,
        requires_approval=True,
        execution_allowed=False,
    )


def decide_recovery(
    starting_exposure: float,
    risk_score: float,
) -> DecisionRecommendation:
    """
    Complete Stage 36 → Stage 37 decision flow.
    """

    comparison = compare_scenarios(
        starting_exposure,
        risk_score,
    )

    return build_decision(comparison)
