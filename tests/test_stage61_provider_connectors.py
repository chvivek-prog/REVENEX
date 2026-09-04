
from revenex.providers import (
    ProviderRegistry,
    ProviderRequest,
    SandboxRecoveryProvider,
    build_idempotency_key,
    normalize_provider_response,
)


def test_sandbox_provider_health():

    provider = SandboxRecoveryProvider()

    response = provider.health()

    assert response.success is True
    assert response.status == "SANDBOX_ONLINE"
    assert response.sandbox is True


def test_sandbox_provider_read():

    provider = SandboxRecoveryProvider()

    response = provider.fetch(
        "invoice",
        "inv-001",
    )

    assert response.success is True
    assert response.status == "SANDBOX_READ_ONLY"
    assert response.data["resource"] == "invoice"
    assert response.data["resource_id"] == "inv-001"


def test_provider_mutation_is_blocked():

    provider = SandboxRecoveryProvider()

    request = ProviderRequest(
        operation="collect_payment",
        idempotency_key="test-key",
        payload={
            "amount": 1000,
        },
    )

    response = provider.execute(request)

    assert response.success is False
    assert response.status == "MUTATION_DISABLED"
    assert response.sandbox is True


def test_registry():

    registry = ProviderRegistry()

    assert "sandbox-recovery" in registry.names()

    provider = registry.get(
        "sandbox-recovery"
    )

    assert provider.name == "sandbox-recovery"


def test_normalization():

    provider = SandboxRecoveryProvider()

    response = provider.fetch(
        "payment",
        "pay-001",
    )

    normalized = normalize_provider_response(
        response
    )

    assert normalized["provider"] == (
        "sandbox-recovery"
    )

    assert normalized["success"] is True
    assert normalized["sandbox"] is True


def test_idempotency_is_deterministic():

    payload = {
        "amount": 1000,
        "invoice_id": "inv-1",
    }

    first = build_idempotency_key(
        "collect_payment",
        payload,
    )

    second = build_idempotency_key(
        "collect_payment",
        payload,
    )

    assert first == second


def test_provider_capabilities():

    provider = SandboxRecoveryProvider()

    capabilities = provider.capabilities

    assert capabilities.sandbox is True
    assert capabilities.mutations_enabled is False

    assert "invoice" in (
        capabilities.read_operations
    )

    assert "collect_payment" in (
        capabilities.mutation_operations
    )
