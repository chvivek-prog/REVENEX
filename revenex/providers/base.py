
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from revenex.providers.contracts import (
    ProviderCapabilities,
    ProviderRequest,
    ProviderResponse,
)


class ProviderConnector(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ProviderResponse:
        raise NotImplementedError

    @abstractmethod
    def fetch(
        self,
        resource: str,
        resource_id: str | None = None,
    ) -> ProviderResponse:
        raise NotImplementedError

    def execute(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        # Financial/provider mutation is deliberately blocked.
        return ProviderResponse(
            provider=self.name,
            operation=request.operation,
            success=False,
            status="MUTATION_DISABLED",
            data={},
            error=(
                "Provider mutation is disabled by the "
                "REVENEX safety boundary."
            ),
            sandbox=self.capabilities.sandbox,
        )

    def normalize(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return dict(payload)
