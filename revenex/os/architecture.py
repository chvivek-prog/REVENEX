
"""
REVENEX Phase 20 — Autonomous Revenue OS.

Final governed architecture:

Observe
    ↓
Understand
    ↓
Predict
    ↓
Simulate
    ↓
Decide
    ↓
Human Approval
    ↓
Safely Act
    ↓
Monitor
    ↓
Outcome
    ↓
Learn
    ↓
Audit
    ↺

Phase 20 establishes the operating-system level contract.

This module is an orchestration/state model only.

It does NOT:
- execute financial actions
- mutate provider state
- mutate models automatically
- bypass human approval
- invent outcomes
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class RevenueOSStage(str, Enum):
    OBSERVE = "OBSERVE"
    UNDERSTAND = "UNDERSTAND"
    PREDICT = "PREDICT"
    SIMULATE = "SIMULATE"
    DECIDE = "DECIDE"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    SAFELY_ACT = "SAFELY_ACT"
    MONITOR = "MONITOR"
    OUTCOME = "OUTCOME"
    LEARN = "LEARN"
    AUDIT = "AUDIT"


class RevenueOSState(str, Enum):
    INTELLIGENCE = "INTELLIGENCE"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    MONITORING = "MONITORING"
    LEARNING = "LEARNING"
    AUDITED = "AUDITED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class AutonomousRevenueOS:
    """
    Governed Autonomous Revenue OS state.

    The OS may progress through intelligence stages, but
    consequential execution remains behind explicit governance.
    """

    decision_id: str

    current_stage: RevenueOSStage
    state: RevenueOSState

    pipeline: tuple[str, ...]

    execution_allowed: bool
    automatic_action: bool
    financial_mutation: bool
    provider_mutation: bool

    human_approval_required: bool
    model_mutation_allowed: bool

    outcome_required_for_learning: bool

    safety_reason: str

    @property
    def is_governed(self) -> bool:
        return (
            self.human_approval_required
            and not self.automatic_action
            and not self.financial_mutation
            and not self.provider_mutation
        )


PIPELINE = (
    RevenueOSStage.OBSERVE.value,
    RevenueOSStage.UNDERSTAND.value,
    RevenueOSStage.PREDICT.value,
    RevenueOSStage.SIMULATE.value,
    RevenueOSStage.DECIDE.value,
    RevenueOSStage.HUMAN_APPROVAL.value,
    RevenueOSStage.SAFELY_ACT.value,
    RevenueOSStage.MONITOR.value,
    RevenueOSStage.OUTCOME.value,
    RevenueOSStage.LEARN.value,
    RevenueOSStage.AUDIT.value,
)


def build_revenue_os(
    decision_id: str,
    *,
    stage: RevenueOSStage = RevenueOSStage.OBSERVE,
    state: RevenueOSState = RevenueOSState.INTELLIGENCE,
) -> AutonomousRevenueOS:
    """
    Build a governed Revenue OS state.

    Phase 20 intentionally starts with execution disabled.
    """

    if stage == RevenueOSStage.HUMAN_APPROVAL:
        state = RevenueOSState.AWAITING_APPROVAL

    elif stage == RevenueOSStage.SAFELY_ACT:
        state = RevenueOSState.EXECUTING

    elif stage == RevenueOSStage.MONITOR:
        state = RevenueOSState.MONITORING

    elif stage == RevenueOSStage.OUTCOME:
        state = RevenueOSState.MONITORING

    elif stage == RevenueOSStage.LEARN:
        state = RevenueOSState.LEARNING

    elif stage == RevenueOSStage.AUDIT:
        state = RevenueOSState.AUDITED

    return AutonomousRevenueOS(
        decision_id=str(decision_id),
        current_stage=stage,
        state=state,
        pipeline=PIPELINE,
        execution_allowed=False,
        automatic_action=False,
        financial_mutation=False,
        provider_mutation=False,
        human_approval_required=True,
        model_mutation_allowed=False,
        outcome_required_for_learning=True,
        safety_reason=(
            "Phase 20 remains governed, read-only, and "
            "human-controlled. Consequential execution is "
            "disabled until separately authorized."
        ),
    )


def revenue_os_to_dict(
    os_state: AutonomousRevenueOS,
) -> dict[str, Any]:
    payload = asdict(os_state)

    payload["current_stage"] = (
        os_state.current_stage.value
    )

    payload["state"] = (
        os_state.state.value
    )

    payload["pipeline"] = list(
        os_state.pipeline
    )

    payload["governed"] = (
        os_state.is_governed
    )

    return payload
