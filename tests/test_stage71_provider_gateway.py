from revenex.provider_gateway import (
    GatewayError,
    GatewayRequest,
    ProviderGateway,
    ProviderOperation,
    ProviderGatewayPolicy,
    RetryPolicy,
    TimeoutPolicy,
)


def test_razorpay_read_only_get():
    gateway = ProviderGateway()

    response = gateway.execute(
        GatewayRequest(
            provider="razorpay",
            operation=ProviderOperation.GET_PAYMENT,
            resource_id="pay_test_1",
        )
    )

    assert response.success is True
    assert response.provider == "razorpay"
    assert response.read_only is True
    assert response.financial_mutation is False
    assert response.provider_mutation is False
    assert response.data["provider_call"] is False


def test_mutation_is_blocked():
    gateway = ProviderGateway()

    response = gateway.execute_mutation(
        GatewayRequest(
            provider="razorpay",
            operation=ProviderOperation.GET_PAYMENT,
            resource_id="pay_test_1",
        )
    )

    assert response.success is False
    assert response.error == GatewayError.MUTATION_BLOCKED
    assert response.read_only is True
    assert response.financial_mutation is False
    assert response.provider_mutation is False


def test_gateway_safety_boundary():
    gateway = ProviderGateway()

    assert gateway.safety == {
        "execution_allowed": False,
        "automatic_action": False,
        "financial_mutation": False,
        "provider_mutation": False,
        "human_approval_required": True,
    }


def test_retry_policy():
    policy = RetryPolicy(
        max_attempts=5,
        base_delay_seconds=0.0,
    )

    assert policy.max_attempts == 5


def test_timeout_policy():
    policy = TimeoutPolicy(
        timeout_seconds=15.0,
    )

    assert policy.timeout_seconds == 15.0


def test_circuit_breaker():
    gateway = ProviderGateway(
        policy=ProviderGatewayPolicy(
            failure_threshold=1,
        )
    )

    gateway.circuit_breaker.record_failure()

    assert gateway.circuit_breaker.is_open is True

    response = gateway.execute(
        GatewayRequest(
            provider="razorpay",
            operation=ProviderOperation.GET_PAYMENT,
            resource_id="pay_test_2",
        )
    )

    assert response.success is False
    assert response.error == GatewayError.CIRCUIT_OPEN


def test_unknown_provider_is_rejected():
    gateway = ProviderGateway()

    response = gateway.execute(
        GatewayRequest(
            provider="unknown-provider",
            operation=ProviderOperation.GET_PAYMENT,
        )
    )

    assert response.success is False
    assert response.error == (
        GatewayError.UNSUPPORTED_OPERATION
    )


def test_idempotency_key_is_supported():
    request = GatewayRequest(
        provider="razorpay",
        operation=ProviderOperation.GET_PAYMENT,
        resource_id="pay_test_3",
        idempotency_key="rev-test-001",
    )

    assert request.idempotency_key == "rev-test-001"
