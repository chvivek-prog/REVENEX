
from __future__ import annotations

from revenex.providers.base import ProviderConnector
from revenex.providers.sandbox import SandboxRecoveryProvider


class ProviderRegistry:

    def __init__(
        self,
        providers: list[ProviderConnector] | None = None,
    ) -> None:

        self._providers = {}

        for provider in (
            providers
            if providers is not None
            else [SandboxRecoveryProvider()]
        ):
            self.register(provider)

    def register(
        self,
        provider: ProviderConnector,
    ) -> None:
        name = provider.name

        if not name:
            raise ValueError(
                "Provider name cannot be empty."
            )

        self._providers[name] = provider

    def get(
        self,
        name: str,
    ) -> ProviderConnector:

        try:
            return self._providers[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown provider: {name}"
            ) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(
            sorted(self._providers.keys())
        )

    def health(self) -> dict:
        return {
            name: self._providers[name]
            .health()
            .status
            for name in self.names()
        }
