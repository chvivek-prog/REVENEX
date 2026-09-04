
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PaymentLinkState(str, Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PaymentLinkIntelligence:
    payment_link_id: str
    state: PaymentLinkState
    amount: float
    amount_paid: float
    amount_remaining: float
    collection_probability: float
    read_only: bool = True
    financial_mutation: bool = False


def analyze_payment_links(
    links: list[dict[str, Any]],
) -> tuple[PaymentLinkIntelligence, ...]:
    result = []

    for link in links:
        amount = max(0.0, float(link.get("amount", 0.0)))
        paid = max(
            0.0,
            min(
                amount,
                float(link.get("amount_paid", 0.0)),
            ),
        )

        raw_status = str(
            link.get("status", "created")
        ).upper()

        mapping = {
            "CREATED": PaymentLinkState.CREATED,
            "PAID": PaymentLinkState.PAID,
            "PARTIALLY_PAID": PaymentLinkState.PARTIALLY_PAID,
            "CANCELLED": PaymentLinkState.CANCELLED,
            "EXPIRED": PaymentLinkState.EXPIRED,
        }

        state = mapping.get(
            raw_status,
            PaymentLinkState.UNKNOWN,
        )

        if state == PaymentLinkState.PAID:
            probability = 1.0
        elif amount <= 0:
            probability = 0.0
        elif state == PaymentLinkState.PARTIALLY_PAID:
            probability = paid / amount
        elif state in (
            PaymentLinkState.CANCELLED,
            PaymentLinkState.EXPIRED,
        ):
            probability = 0.0
        else:
            probability = max(
                0.0,
                min(1.0, paid / amount),
            )

        result.append(
            PaymentLinkIntelligence(
                payment_link_id=str(
                    link.get(
                        "payment_link_id",
                        link.get("id", ""),
                    )
                ),
                state=state,
                amount=amount,
                amount_paid=paid,
                amount_remaining=max(
                    0.0,
                    amount - paid,
                ),
                collection_probability=probability,
            )
        )

    return tuple(result)
