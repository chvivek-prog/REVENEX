
"""
REVENEX Phase 15 — Decision Intelligence.

Converts simulation results into a complete, explainable,
deterministic decision object.

This module does NOT execute decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from revenex.simulation.advanced import (
    SimulationResult,
    SimulationScenario,
)


@dataclass(frozen=True)
class DecisionAlternative:
    scenario: str
    expected_collection: float
    remaining_exposure: float
    risk: str
    confidence: float


@dataclass(frozen=True)
class DecisionIntelligence:
    decision_id: str

    recommended_action: str
    confidence: float

    expected_impact: float
    remaining_exposure: float
    risk: str

    evidence: tuple[str, ...]
    alternatives: tuple[DecisionAlternative, ...]

    why: str

    approval_required: bool

    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False
    human_approval_required: bool = True


def _action_for_scenario(
    scenario: SimulationScenario,
) -> str:

    actions = {
        SimulationScenario.CONSERVATIVE:
            "CONSERVATIVE_RECOVERY_REVIEW",

        SimulationScenario.BALANCED:
            "BALANCED_RECOVERY_REVIEW",

        SimulationScenario.AGGRESSIVE:
            "AGGRESSIVE_RECOVERY_REVIEW",

        SimulationScenario.CUSTOM:
            "CUSTOM_STRATEGY_REVIEW",
    }

    return actions[scenario]


def _risk_rank(risk: str) -> int:

    return {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
    }.get(
        str(risk).upper(),
        2,
    )


def build_decision(
    simulations: tuple[SimulationResult, ...],
    *,
    decision_id: str = "decision-intelligence",
) -> DecisionIntelligence:
    """
    Select the best simulation using a deterministic decision rule.

    Primary objective:
        maximize expected collection.

    Secondary objective:
        maximize confidence.

    The selected result is still only a recommendation.
    """

    if not simulations:
        return DecisionIntelligence(
            decision_id=decision_id,
            recommended_action="MONITOR",
            confidence=0.0,
            expected_impact=0.0,
            remaining_exposure=0.0,
            risk="LOW",
            evidence=(
                "No simulations were supplied.",
                "No financial decision was generated.",
            ),
            alternatives=(),
            why=(
                "REVENEX requires simulation evidence "
                "before recommending an action."
            ),
            approval_required=True,
        )

    ranked = sorted(
        simulations,
        key=lambda item: (
            item.expected_collection,
            item.confidence,
            -_risk_rank(
                item.risk.value
            ),
        ),
        reverse=True,
    )

    selected = ranked[0]

    alternatives = tuple(
        DecisionAlternative(
            scenario=result.scenario.value,
            expected_collection=(
                result.expected_collection
            ),
            remaining_exposure=(
                result.remaining_exposure
            ),
            risk=result.risk.value,
            confidence=result.confidence,
        )
        for result in simulations
        if result.scenario != selected.scenario
    )

    evidence = (
        f"selected_scenario="
        f"{selected.scenario.value}",

        f"expected_collection="
        f"{selected.expected_collection:.2f}",

        f"remaining_exposure="
        f"{selected.remaining_exposure:.2f}",

        f"confidence="
        f"{selected.confidence:.4f}",

        f"risk="
        f"{selected.risk.value}",

        "recommendation=READ_ONLY",

        "execution_allowed=false",

        "human_approval_required=true",
    )

    why = (
        f"{selected.scenario.value} produced the highest "
        f"simulated expected collection of "
        f"₹{selected.expected_collection:,.2f} "
        f"among the available scenarios. "
        f"The simulation confidence is "
        f"{selected.confidence:.0%} and the assessed "
        f"risk is {selected.risk.value}. "
        f"REVENEX therefore recommends "
        f"{_action_for_scenario(selected.scenario)}, "
        f"subject to human approval."
    )

    return DecisionIntelligence(
        decision_id=decision_id,
        recommended_action=(
            _action_for_scenario(
                selected.scenario
            )
        ),
        confidence=selected.confidence,
        expected_impact=(
            selected.expected_collection
        ),
        remaining_exposure=(
            selected.remaining_exposure
        ),
        risk=selected.risk.value,
        evidence=evidence,
        alternatives=alternatives,
        why=why,
        approval_required=True,
    )


def decision_to_dict(
    decision: DecisionIntelligence,
) -> dict[str, Any]:

    return {
        "decision_id":
            decision.decision_id,

        "recommended_action":
            decision.recommended_action,

        "confidence":
            decision.confidence,

        "expected_impact":
            decision.expected_impact,

        "remaining_exposure":
            decision.remaining_exposure,

        "risk":
            decision.risk,

        "evidence":
            list(decision.evidence),

        "alternatives": [
            {
                "scenario":
                    item.scenario,

                "expected_collection":
                    item.expected_collection,

                "remaining_exposure":
                    item.remaining_exposure,

                "risk":
                    item.risk,

                "confidence":
                    item.confidence,
            }
            for item in decision.alternatives
        ],

        "why":
            decision.why,

        "approval_required":
            decision.approval_required,

        "governance": {
            "read_only":
                decision.read_only,

            "execution_allowed":
                decision.execution_allowed,

            "automatic_action":
                decision.automatic_action,

            "financial_mutation":
                decision.financial_mutation,

            "provider_mutation":
                decision.provider_mutation,

            "human_approval_required":
                decision.human_approval_required,
        },
    }
