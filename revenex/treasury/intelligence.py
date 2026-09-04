
from __future__ import annotations

from typing import Any


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def build_treasury_intelligence(
    *,
    captured_payment_value: float = 0.0,
    refund_value: float = 0.0,
    pending_settlement_value: float = 0.0,
    pending_payout_value: float = 0.0,
    receivables_exposure: float = 0.0,
) -> dict[str, Any]:
    """
    Deterministic treasury intelligence.

    This is a cash-position view, not a banking operation.
    """

    captured = _money(captured_payment_value)
    refunds = _money(refund_value)
    settlements = _money(pending_settlement_value)
    payouts = _money(pending_payout_value)
    receivables = _money(receivables_exposure)

    available_inflow = max(
        0.0,
        captured - refunds,
    )

    committed_outflow = (
        settlements + payouts
    )

    near_term_cash_position = (
        available_inflow
        - committed_outflow
    )

    liquidity_exposure = (
        settlements
        + payouts
        + receivables
    )

    if near_term_cash_position < 0:
        liquidity_signal = "LIQUIDITY_PRESSURE"
    elif liquidity_exposure > available_inflow:
        liquidity_signal = "LIQUIDITY_REVIEW"
    else:
        liquidity_signal = "LIQUIDITY_STABLE"

    return {
        "captured_inflow": round(captured, 2),
        "refund_outflow": round(refunds, 2),
        "pending_settlement_commitment": round(
            settlements,
            2,
        ),
        "pending_payout_commitment": round(
            payouts,
            2,
        ),
        "receivables_exposure": round(
            receivables,
            2,
        ),
        "available_inflow": round(
            available_inflow,
            2,
        ),
        "committed_outflow": round(
            committed_outflow,
            2,
        ),
        "near_term_cash_position": round(
            near_term_cash_position,
            2,
        ),
        "liquidity_exposure": round(
            liquidity_exposure,
            2,
        ),
        "liquidity_signal": liquidity_signal,
        "read_only": True,
    }
