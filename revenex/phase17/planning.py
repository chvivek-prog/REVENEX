from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ScenarioType(str, Enum):
    BASELINE = "BASELINE"
    CONSERVATIVE = "CONSERVATIVE"
    BALANCED = "BALANCED"
    AGGRESSIVE = "AGGRESSIVE"
    STRESS = "STRESS"


@dataclass(frozen=True)
class ScenarioResult:
    scenario: ScenarioType
    expected_collection: float
    remaining_exposure: float
    recovery_rate: float
    incremental_collection: float
    downside_exposure: float
    confidence: float
    interpretation: str
    evidence_refs: tuple[str, ...]

    read_only: bool = True
    human_review_required: bool = True


@dataclass(frozen=True)
class PlanningReport:
    baseline_collection: float
    current_exposure: float

    scenarios: tuple[ScenarioResult, ...]
    selected_scenario: ScenarioType

    best_expected_collection: float
    worst_remaining_exposure: float
    scenario_spread: float

    planning_summary: str

    read_only: bool = True
    human_review_required: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


# Recovery assumptions are intentionally deterministic.
# They represent planning scenarios, not guaranteed outcomes.
_RECOVERY_RATES = {
    ScenarioType.BASELINE: 0.45,
    ScenarioType.CONSERVATIVE: 0.55,
    ScenarioType.BALANCED: 0.70,
    ScenarioType.AGGRESSIVE: 0.88,
    ScenarioType.STRESS: 0.30,
}

_CONFIDENCE = {
    ScenarioType.BASELINE: 0.80,
    ScenarioType.CONSERVATIVE: 0.74,
    ScenarioType.BALANCED: 0.70,
    ScenarioType.AGGRESSIVE: 0.62,
    ScenarioType.STRESS: 0.48,
}


def _money(value: Any) -> float:
    try:
        return max(0.0, round(float(value or 0), 2))
    except (TypeError, ValueError):
        return 0.0


def _confidence(value: Any) -> float:
    try:
        return round(
            min(max(float(value), 0.0), 1.0),
            4,
        )
    except (TypeError, ValueError):
        return 0.0


def _interpretation(
    scenario: ScenarioType,
    expected: float,
    remaining: float,
) -> str:
    if scenario == ScenarioType.STRESS:
        return (
            f"Stress planning projects ₹{expected:,.2f} collection "
            f"with ₹{remaining:,.2f} remaining exposure."
        )

    if scenario == ScenarioType.AGGRESSIVE:
        return (
            f"Aggressive planning projects ₹{expected:,.2f} collection "
            f"with ₹{remaining:,.2f} remaining exposure."
        )

    if scenario == ScenarioType.BALANCED:
        return (
            f"Balanced planning projects ₹{expected:,.2f} collection "
            f"with ₹{remaining:,.2f} remaining exposure."
        )

    if scenario == ScenarioType.CONSERVATIVE:
        return (
            f"Conservative planning projects ₹{expected:,.2f} collection "
            f"with ₹{remaining:,.2f} remaining exposure."
        )

    return (
        f"Baseline planning projects ₹{expected:,.2f} collection "
        f"with ₹{remaining:,.2f} remaining exposure."
    )


def run_strategic_scenarios(
    *,
    current_exposure: float,
    baseline_collection: float,
    selected_scenario: ScenarioType = ScenarioType.AGGRESSIVE,
) -> PlanningReport:

    exposure = _money(current_exposure)
    baseline = min(
        _money(baseline_collection),
        exposure,
    )

    scenarios: list[ScenarioResult] = []

    for scenario in ScenarioType:
        rate = _RECOVERY_RATES[scenario]

        expected = round(
            min(
                exposure,
                exposure * rate,
            ),
            2,
        )

        remaining = round(
            max(exposure - expected, 0.0),
            2,
        )

        incremental = round(
            max(expected - baseline, 0.0),
            2,
        )

        downside = round(
            max(
                baseline - expected,
                0.0,
            ),
            2,
        )

        confidence = _confidence(
            _CONFIDENCE[scenario]
        )

        scenarios.append(
            ScenarioResult(
                scenario=scenario,
                expected_collection=expected,
                remaining_exposure=remaining,
                recovery_rate=rate,
                incremental_collection=incremental,
                downside_exposure=downside,
                confidence=confidence,
                interpretation=_interpretation(
                    scenario,
                    expected,
                    remaining,
                ),
                evidence_refs=(
                    "current_exposure",
                    "baseline_collection",
                    f"recovery_rate:{rate}",
                    f"scenario:{scenario.value}",
                ),
            )
        )

    selected = next(
        result
        for result in scenarios
        if result.scenario == selected_scenario
    )

    best_collection = max(
        result.expected_collection
        for result in scenarios
    )

    worst_remaining = max(
        result.remaining_exposure
        for result in scenarios
    )

    scenario_spread = round(
        max(
            result.expected_collection
            for result in scenarios
        )
        - min(
            result.expected_collection
            for result in scenarios
        ),
        2,
    )

    planning_summary = (
        f"Five deterministic planning scenarios were evaluated. "
        f"{selected.scenario.value} projects "
        f"₹{selected.expected_collection:,.2f} collection and "
        f"₹{selected.remaining_exposure:,.2f} remaining exposure. "
        f"Scenario spread is ₹{scenario_spread:,.2f}. "
        f"All results are advisory and require human review."
    )

    return PlanningReport(
        baseline_collection=baseline,
        current_exposure=exposure,
        scenarios=tuple(scenarios),
        selected_scenario=selected_scenario,
        best_expected_collection=best_collection,
        worst_remaining_exposure=worst_remaining,
        scenario_spread=scenario_spread,
        planning_summary=planning_summary,
    )
