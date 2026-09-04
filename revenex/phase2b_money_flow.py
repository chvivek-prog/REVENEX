from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _money(value: Any) -> float:
    try:
        return round(max(0.0, float(value or 0)), 2)
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class MoneyFlow:
    invoice_amount: float
    collected_amount: float
    settled_amount: float
    fees: float
    tax: float
    net_cash: float
    outstanding: float
    unexplained_variance: float
    human_review_required: bool
    read_only: bool
    execution_allowed: bool
    financial_mutation: bool
    provider_mutation: bool


def analyze_money_flow(record: dict[str, Any]) -> MoneyFlow:
    invoice = _money(
        record.get("invoice_amount")
        or record.get("amount")
    )

    collected = _money(
        record.get("collected_amount")
        or record.get("payment_amount")
    )

    settled = _money(
        record.get("settled_amount")
        or record.get("settlement_amount")
    )

    fees = _money(
        record.get("fees")
        or record.get("fee")
        or record.get("settlement_fee")
    )

    tax = _money(
        record.get("tax")
        or record.get("tax_amount")
    )

    net_cash = round(max(0.0, settled - fees - tax), 2)

    outstanding = round(
        max(0.0, invoice - collected),
        2,
    )

    expected_net = round(
        max(0.0, collected - fees - tax),
        2,
    )

    unexplained_variance = round(
        max(0.0, expected_net - net_cash),
        2,
    )

    human_review = (
        unexplained_variance > 0
        or settled > collected
        or collected > invoice
    )

    return MoneyFlow(
        invoice_amount=invoice,
        collected_amount=collected,
        settled_amount=settled,
        fees=fees,
        tax=tax,
        net_cash=net_cash,
        outstanding=outstanding,
        unexplained_variance=unexplained_variance,
        human_review_required=human_review,
        read_only=True,
        execution_allowed=False,
        financial_mutation=False,
        provider_mutation=False,
    )
