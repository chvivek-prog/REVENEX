
from __future__ import annotations

from typing import Any

from revenex.providers.base import ProviderConnector
from revenex.providers.contracts import (
    ProviderCapabilities,
    ProviderResponse,
)


class SandboxRecoveryProvider(ProviderConnector):

    @property
    def name(self) -> str:
        return "sandbox-recovery"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self.name,
            sandbox=True,
            read_operations=(
                "health",
                "invoice",
                "payment",
                "customer",
                "order",
                "subscription",
                "refund",
                "settlement",
                "dispute",
                "payout",
            ),
            mutation_operations=(
                "collect_payment",
                "refund_payment",
                "create_payout",
                "cancel_subscription",
            ),
            mutations_enabled=False,
        )

    def health(self) -> ProviderResponse:
        return ProviderResponse(
            provider=self.name,
            operation="health",
            success=True,
            status="SANDBOX_ONLINE",
            data={
                "provider": self.name,
                "sandbox": True,
                "read_only": True,
            },
            sandbox=True,
        )

    def fetch(
        self,
        resource: str,
        resource_id: str | None = None,
    ) -> ProviderResponse:

        allowed = set(
            self.capabilities.read_operations
        )

        if resource not in allowed:
            return ProviderResponse(
                provider=self.name,
                operation=f"fetch:{resource}",
                success=False,
                status="UNSUPPORTED_RESOURCE",
                data={},
                error=(
                    f"Unsupported provider resource: "
                    f"{resource}"
                ),
                sandbox=True,
            )

        return ProviderResponse(
            provider=self.name,
            operation=f"fetch:{resource}",
            success=True,
            status="SANDBOX_READ_ONLY",
            data={
                "resource": resource,
                "resource_id": resource_id,
                "sandbox": True,
                "mutation": False,
            },
            sandbox=True,
        )

    def normalize(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "provider": self.name,
            "sandbox": True,
            "resource": payload.get("resource"),
            "resource_id": payload.get("resource_id"),
            "data": dict(payload),
        }
