
"""
REVENEX Phase 17 — Safe Autonomous Execution Gateway.

Architecture:

AI
 ↓
Decision
 ↓
Policy Engine
 ↓
Risk Limits
 ↓
Human Approval
 ↓
Execution Gateway
 ↓
Idempotency
 ↓
Provider
 ↓
Webhook
 ↓
Verification
 ↓
Outcome

Development safety:
    No financial execution is enabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class ExecutionStatus(str, Enum):
    BLOCKED = "BLOCKED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class ExecutionBlockReason(str, Enum):
    EXECUTION_DISABLED = "EXECUTION_DISABLED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    RISK_LIMIT_EXCEEDED = "RISK_LIMIT_EXCEEDED"
    DUPLICATE_REQUEST = "DUPLICATE_REQUEST"
    PROVIDER_MUTATION_DISABLED = "PROVIDER_MUTATION_DISABLED"


@dataclass(frozen=True)
class ExecutionPolicy:
    execution_enabled: bool = False
    provider_mutation_enabled: bool = False
    automatic_action_enabled: bool = False
    human_approval_required: bool = True
    max_execution_amount: float = 0.0


@dataclass(frozen=True)
class ExecutionRequest:
    execution_id: str
    decision_id: str
    approval_id: str
    action: str
    amount: float
    idempotency_key: str
    provider: str


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    decision_id: str
    status: ExecutionStatus
    executed: bool
    provider_called: bool
    financial_mutation: bool
    idempotency_key: str
    reason: str


class ProviderGateway(Protocol):

    def execute(
        self,
        request: ExecutionRequest,
    ) -> dict[str, Any]:
        ...


class InMemoryIdempotencyStore:
    """
    Deterministic idempotency registry.

    It intentionally stores execution keys only.
    It never stores or mutates financial state.
    """

    def __init__(self) -> None:
        self._keys: set[str] = set()

    def exists(
        self,
        key: str,
    ) -> bool:
        return key in self._keys

    def reserve(
        self,
        key: str,
    ) -> bool:
        if key in self._keys:
            return False

        self._keys.add(key)
        return True


def validate_execution_request(
    request: ExecutionRequest,
) -> tuple[bool, str]:

    if not request.execution_id.strip():
        return False, "execution_id is required."

    if not request.decision_id.strip():
        return False, "decision_id is required."

    if not request.approval_id.strip():
        return False, "approval_id is required."

    if not request.action.strip():
        return False, "action is required."

    if not request.idempotency_key.strip():
        return False, "idempotency_key is required."

    if request.amount < 0:
        return False, "amount cannot be negative."

    if not request.provider.strip():
        return False, "provider is required."

    return True, ""


def authorize_execution(
    *,
    request: ExecutionRequest,
    policy: ExecutionPolicy,
    approval_status: str,
    idempotency_store: InMemoryIdempotencyStore,
) -> ExecutionResult:
    """
    Safety gate.

    The default policy cannot execute anything.
    """

    valid, error = validate_execution_request(
        request
    )

    if not valid:
        return ExecutionResult(
            execution_id=request.execution_id,
            decision_id=request.decision_id,
            status=ExecutionStatus.BLOCKED,
            executed=False,
            provider_called=False,
            financial_mutation=False,
            idempotency_key=request.idempotency_key,
            reason=error,
        )

    if idempotency_store.exists(
        request.idempotency_key
    ):
        return ExecutionResult(
            execution_id=request.execution_id,
            decision_id=request.decision_id,
            status=ExecutionStatus.BLOCKED,
            executed=False,
            provider_called=False,
            financial_mutation=False,
            idempotency_key=request.idempotency_key,
            reason=(
                ExecutionBlockReason.DUPLICATE_REQUEST.value
            ),
        )

    if not policy.execution_enabled:
        return ExecutionResult(
            execution_id=request.execution_id,
            decision_id=request.decision_id,
            status=ExecutionStatus.BLOCKED,
            executed=False,
            provider_called=False,
            financial_mutation=False,
            idempotency_key=request.idempotency_key,
            reason=(
                ExecutionBlockReason.EXECUTION_DISABLED.value
            ),
        )

    if not policy.provider_mutation_enabled:
        return ExecutionResult(
            execution_id=request.execution_id,
            decision_id=request.decision_id,
            status=ExecutionStatus.BLOCKED,
            executed=False,
            provider_called=False,
            financial_mutation=False,
            idempotency_key=request.idempotency_key,
            reason=(
                ExecutionBlockReason.PROVIDER_MUTATION_DISABLED.value
            ),
        )

    if policy.human_approval_required:
        if approval_status != "APPROVED":
            return ExecutionResult(
                execution_id=request.execution_id,
                decision_id=request.decision_id,
                status=ExecutionStatus.PENDING_APPROVAL,
                executed=False,
                provider_called=False,
                financial_mutation=False,
                idempotency_key=request.idempotency_key,
                reason=(
                    ExecutionBlockReason.HUMAN_APPROVAL_REQUIRED.value
                ),
            )

    if request.amount > policy.max_execution_amount:
        return ExecutionResult(
            execution_id=request.execution_id,
            decision_id=request.decision_id,
            status=ExecutionStatus.BLOCKED,
            executed=False,
            provider_called=False,
            financial_mutation=False,
            idempotency_key=request.idempotency_key,
            reason=(
                ExecutionBlockReason.RISK_LIMIT_EXCEEDED.value
            ),
        )

    if not idempotency_store.reserve(
        request.idempotency_key
    ):
        return ExecutionResult(
            execution_id=request.execution_id,
            decision_id=request.decision_id,
            status=ExecutionStatus.BLOCKED,
            executed=False,
            provider_called=False,
            financial_mutation=False,
            idempotency_key=request.idempotency_key,
            reason=(
                ExecutionBlockReason.DUPLICATE_REQUEST.value
            ),
        )

    # This branch is deliberately unreachable with the
    # development policy above.
    return ExecutionResult(
        execution_id=request.execution_id,
        decision_id=request.decision_id,
        status=ExecutionStatus.APPROVED,
        executed=False,
        provider_called=False,
        financial_mutation=False,
        idempotency_key=request.idempotency_key,
        reason="Execution authorized by policy.",
    )


def execution_to_dict(
    result: ExecutionResult,
) -> dict[str, Any]:

    return {
        "execution_id": result.execution_id,
        "decision_id": result.decision_id,
        "status": result.status.value,
        "executed": result.executed,
        "provider_called": result.provider_called,
        "financial_mutation": result.financial_mutation,
        "idempotency_key": result.idempotency_key,
        "reason": result.reason,
        "safety": {
            "execution_allowed": result.executed,
            "provider_called": result.provider_called,
            "financial_mutation": result.financial_mutation,
        },
    }
