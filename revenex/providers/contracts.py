
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderRequest:
    operation: str
    idempotency_key: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    operation: str
    success: bool
    status: str
    data: dict[str, Any]
    error: str | None = None
    request_id: str | None = None
    sandbox: bool = True


@dataclass(frozen=True)
class ProviderCapabilities:
    provider: str
    sandbox: bool
    read_operations: tuple[str, ...]
    mutation_operations: tuple[str, ...]
    mutations_enabled: bool
