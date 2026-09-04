
from revenex.execution.gateway import (
    ExecutionBlockReason,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    InMemoryIdempotencyStore,
    authorize_execution,
)


def request(
    key="idem-1",
):
    return ExecutionRequest(
        execution_id="exec-1",
        decision_id="decision-1",
        approval_id="approval-1",
        action="AGGRESSIVE_RECOVERY_REVIEW",
        amount=100000,
        idempotency_key=key,
        provider="razorpay",
    )


def test_execution_disabled_by_default():

    result = authorize_execution(
        request=request(),
        policy=ExecutionPolicy(),
        approval_status="APPROVED",
        idempotency_store=InMemoryIdempotencyStore(),
    )

    assert result.status == ExecutionStatus.BLOCKED
    assert result.executed is False
    assert result.provider_called is False
    assert result.financial_mutation is False
    assert (
        result.reason
        == ExecutionBlockReason.EXECUTION_DISABLED.value
    )


def test_human_approval_required():

    policy = ExecutionPolicy(
        execution_enabled=True,
        provider_mutation_enabled=True,
        automatic_action_enabled=False,
        human_approval_required=True,
        max_execution_amount=200000,
    )

    result = authorize_execution(
        request=request(),
        policy=policy,
        approval_status="PENDING",
        idempotency_store=InMemoryIdempotencyStore(),
    )

    assert (
        result.status
        == ExecutionStatus.PENDING_APPROVAL
    )

    assert result.executed is False
    assert result.provider_called is False
    assert result.financial_mutation is False


def test_provider_mutation_is_blocked():

    policy = ExecutionPolicy(
        execution_enabled=True,
        provider_mutation_enabled=False,
        human_approval_required=False,
        max_execution_amount=200000,
    )

    result = authorize_execution(
        request=request(),
        policy=policy,
        approval_status="APPROVED",
        idempotency_store=InMemoryIdempotencyStore(),
    )

    assert result.status == ExecutionStatus.BLOCKED

    assert (
        result.reason
        == ExecutionBlockReason.PROVIDER_MUTATION_DISABLED.value
    )


def test_risk_limit_blocks_execution():

    policy = ExecutionPolicy(
        execution_enabled=True,
        provider_mutation_enabled=True,
        human_approval_required=False,
        max_execution_amount=50000,
    )

    result = authorize_execution(
        request=request(),
        policy=policy,
        approval_status="APPROVED",
        idempotency_store=InMemoryIdempotencyStore(),
    )

    assert result.status == ExecutionStatus.BLOCKED

    assert (
        result.reason
        == ExecutionBlockReason.RISK_LIMIT_EXCEEDED.value
    )


def test_duplicate_idempotency_key_is_blocked():

    store = InMemoryIdempotencyStore()

    policy = ExecutionPolicy(
        execution_enabled=False,
    )

    first = authorize_execution(
        request=request("same-key"),
        policy=policy,
        approval_status="APPROVED",
        idempotency_store=store,
    )

    second = authorize_execution(
        request=request("same-key"),
        policy=policy,
        approval_status="APPROVED",
        idempotency_store=store,
    )

    assert first.executed is False
    assert second.executed is False


def test_negative_amount_is_rejected():

    bad = ExecutionRequest(
        execution_id="exec-negative",
        decision_id="decision-negative",
        approval_id="approval-negative",
        action="TEST",
        amount=-1,
        idempotency_key="negative",
        provider="razorpay",
    )

    result = authorize_execution(
        request=bad,
        policy=ExecutionPolicy(),
        approval_status="APPROVED",
        idempotency_store=InMemoryIdempotencyStore(),
    )

    assert result.status == ExecutionStatus.BLOCKED
    assert result.executed is False


def test_execution_gateway_never_mutates_financial_state():

    result = authorize_execution(
        request=request(),
        policy=ExecutionPolicy(),
        approval_status="APPROVED",
        idempotency_store=InMemoryIdempotencyStore(),
    )

    assert result.financial_mutation is False
    assert result.provider_called is False
    assert result.executed is False
