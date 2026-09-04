
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProviderCapability(str, Enum):
    CUSTOMERS = "CUSTOMERS"
    ORDERS = "ORDERS"
    PAYMENTS = "PAYMENTS"
    PAYMENT_LINKS = "PAYMENT_LINKS"
    INVOICES = "INVOICES"
    SUBSCRIPTIONS = "SUBSCRIPTIONS"
    REFUNDS = "REFUNDS"
    SETTLEMENTS = "SETTLEMENTS"
    DISPUTES = "DISPUTES"
    PAYOUTS = "PAYOUTS"
    WEBHOOKS = "WEBHOOKS"
    RECONCILIATION = "RECONCILIATION"


@dataclass(frozen=True)
class ProviderCapabilityMatrix:
    provider: str
    capabilities: tuple[ProviderCapability, ...]
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False

    def supports(
        self,
        capability: ProviderCapability,
    ) -> bool:
        return capability in self.capabilities


RAZORPAY_CAPABILITIES = ProviderCapabilityMatrix(
    provider="razorpay",
    capabilities=tuple(ProviderCapability),
)
