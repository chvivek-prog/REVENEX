from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProviderOperation(str, Enum):
    GET_CUSTOMER = "GET_CUSTOMER"
    GET_ORDER = "GET_ORDER"
    GET_PAYMENT = "GET_PAYMENT"
    GET_PAYMENT_LINK = "GET_PAYMENT_LINK"
    GET_INVOICE = "GET_INVOICE"
    GET_SUBSCRIPTION = "GET_SUBSCRIPTION"
    GET_REFUND = "GET_REFUND"
    GET_SETTLEMENT = "GET_SETTLEMENT"
    GET_DISPUTE = "GET_DISPUTE"
    GET_PAYOUT = "GET_PAYOUT"
    LIST_EVENTS = "LIST_EVENTS"


class GatewayError(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    MUTATION_BLOCKED = "MUTATION_BLOCKED"


@dataclass(frozen=True)
class GatewayRequest:
    provider: str
    operation: ProviderOperation
    resource_id: str | None = None
    parameters: dict[str, Any] | None = None
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError("provider is required")

        if self.resource_id is not None:
            object.__setattr__(
                self,
                "resource_id",
                str(self.resource_id),
            )

        if self.parameters is None:
            object.__setattr__(
                self,
                "parameters",
                {},
            )


@dataclass(frozen=True)
class GatewayResponse:
    provider: str
    operation: ProviderOperation
    success: bool
    data: dict[str, Any]
    error: GatewayError | None = None
    attempts: int = 1
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False
