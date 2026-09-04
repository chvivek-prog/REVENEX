from __future__ import annotations

from .contracts import (
    GatewayError,
    GatewayRequest,
    GatewayResponse,
)
from .policy import (
    CircuitBreaker,
    ProviderGatewayPolicy,
)
from .razorpay import RazorpayProviderAdapter


class ProviderGateway:
    """
    Single governed boundary between REVENEX and providers.

    Phase 22:
      - validates provider requests
      - enforces read-only mode
      - exposes retry/timeout/circuit-breaker policy
      - does not perform live financial mutations
    """

    def __init__(
        self,
        *,
        policy: ProviderGatewayPolicy | None = None,
        razorpay: RazorpayProviderAdapter | None = None,
    ) -> None:
        self.policy = policy or ProviderGatewayPolicy()
        self.razorpay = (
            razorpay or RazorpayProviderAdapter()
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.policy.failure_threshold
        )

    def execute(
        self,
        request: GatewayRequest,
    ) -> GatewayResponse:
        if (
            not self.circuit_breaker.allow_request()
        ):
            return GatewayResponse(
                provider=request.provider,
                operation=request.operation,
                success=False,
                data={},
                error=GatewayError.CIRCUIT_OPEN,
            )

        if request.provider == "razorpay":
            response = self.razorpay.execute(
                request
            )

            if response.success:
                self.circuit_breaker.record_success()
            else:
                self.circuit_breaker.record_failure()

            return response

        return GatewayResponse(
            provider=request.provider,
            operation=request.operation,
            success=False,
            data={},
            error=GatewayError.UNSUPPORTED_OPERATION,
        )

    def execute_mutation(
        self,
        request: GatewayRequest,
    ) -> GatewayResponse:
        return GatewayResponse(
            provider=request.provider,
            operation=request.operation,
            success=False,
            data={},
            error=GatewayError.MUTATION_BLOCKED,
            read_only=True,
            financial_mutation=False,
            provider_mutation=False,
        )

    @property
    def safety(self) -> dict[str, bool]:
        return {
            "execution_allowed": False,
            "automatic_action": False,
            "financial_mutation": (
                self.policy.financial_mutation_allowed
            ),
            "provider_mutation": (
                self.policy.provider_mutation_allowed
            ),
            "human_approval_required": True,
        }
