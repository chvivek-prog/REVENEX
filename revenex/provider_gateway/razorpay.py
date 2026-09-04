from __future__ import annotations

from typing import Any

from .contracts import (
    GatewayError,
    GatewayRequest,
    GatewayResponse,
    ProviderOperation,
)


class RazorpayProviderAdapter:
    """
    Read-only Razorpay provider boundary.

    Phase 22 deliberately does not perform live HTTP calls.
    Live provider connectivity belongs to a later governed phase.
    """

    provider = "razorpay"

    SUPPORTED = frozenset({
        ProviderOperation.GET_CUSTOMER,
        ProviderOperation.GET_ORDER,
        ProviderOperation.GET_PAYMENT,
        ProviderOperation.GET_PAYMENT_LINK,
        ProviderOperation.GET_INVOICE,
        ProviderOperation.GET_SUBSCRIPTION,
        ProviderOperation.GET_REFUND,
        ProviderOperation.GET_SETTLEMENT,
        ProviderOperation.GET_DISPUTE,
        ProviderOperation.GET_PAYOUT,
        ProviderOperation.LIST_EVENTS,
    })

    def execute(
        self,
        request: GatewayRequest,
    ) -> GatewayResponse:
        if request.provider != self.provider:
            return GatewayResponse(
                provider=self.provider,
                operation=request.operation,
                success=False,
                data={},
                error=GatewayError.INVALID_REQUEST,
            )

        if request.operation not in self.SUPPORTED:
            return GatewayResponse(
                provider=self.provider,
                operation=request.operation,
                success=False,
                data={},
                error=GatewayError.UNSUPPORTED_OPERATION,
            )

        # Deliberately return a safe boundary response.
        # No credentials, network calls, or provider mutation occur.
        return GatewayResponse(
            provider=self.provider,
            operation=request.operation,
            success=True,
            data={
                "provider": self.provider,
                "resource_id": request.resource_id,
                "mode": "READ_ONLY_ADAPTER",
                "provider_call": False,
            },
            read_only=True,
            financial_mutation=False,
            provider_mutation=False,
        )

    def execute_mutation(
        self,
        request: GatewayRequest,
    ) -> GatewayResponse:
        return GatewayResponse(
            provider=self.provider,
            operation=request.operation,
            success=False,
            data={},
            error=GatewayError.MUTATION_BLOCKED,
            read_only=True,
            financial_mutation=False,
            provider_mutation=False,
        )
