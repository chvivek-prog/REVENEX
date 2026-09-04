
from __future__ import annotations

from typing import Any


ORDER_STATUSES = {
    "created",
    "attempted",
    "paid",
    "failed",
    "cancelled",
    "expired",
    "refunded",
}


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _status(order: dict[str, Any]) -> str:
    value = str(order.get("status", "")).strip().lower()

    if value:
        return value

    if order.get("paid") is True:
        return "paid"

    if order.get("attempts", 0):
        return "attempted"

    return "created"


def build_order_intelligence(
    orders: list[dict[str, Any]],
    payments: list[dict[str, Any]] | None = None,
    invoices: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Build deterministic read-only order intelligence.

    No order creation, cancellation, capture, refund, or provider
    mutation occurs here.
    """

    payments = payments or []
    invoices = invoices or []

    successful_payment_order_ids = {
        str(
            payment.get("order_id")
            or payment.get("order")
        )
        for payment in payments
        if str(
            payment.get("status", "")
        ).lower() in {
            "captured",
            "paid",
            "success",
            "successful",
        }
    }

    invoice_order_ids = {
        str(
            invoice.get("order_id")
            or invoice.get("order")
        )
        for invoice in invoices
        if invoice.get("order_id") is not None
        or invoice.get("order") is not None
    }

    results = []

    for index, order in enumerate(orders):
        order_id = str(
            order.get("order_id")
            or order.get("id")
            or f"order-{index + 1}"
        )

        customer_id = str(
            order.get("customer_id")
            or order.get("customer")
            or "unknown-customer"
        )

        amount = _money(
            order.get("amount")
            or order.get("amount_paid")
            or order.get("value")
        )

        amount_paid = _money(
            order.get("amount_paid")
        )

        status = _status(order)

        has_successful_payment = (
            order_id in successful_payment_order_ids
            or status == "paid"
            or amount_paid >= amount > 0
        )

        has_invoice = order_id in invoice_order_ids

        if amount > 0:
            realization_ratio = min(
                1.0,
                amount_paid / amount,
            )
        else:
            realization_ratio = (
                1.0 if has_successful_payment else 0.0
            )

        if status in {"paid"} or has_successful_payment:
            risk_level = "LOW"
            signal = "ORDER_REALIZED"
        elif status in {"failed", "cancelled", "expired"}:
            risk_level = "HIGH"
            signal = "ORDER_FAILURE_PRESSURE"
        elif status in {"attempted"}:
            risk_level = "MEDIUM"
            signal = "ORDER_PAYMENT_PENDING"
        else:
            risk_level = "MEDIUM"
            signal = "ORDER_UNREALIZED"

        results.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "amount": round(amount, 2),
                "amount_paid": round(amount_paid, 2),
                "status": status,
                "has_successful_payment": has_successful_payment,
                "has_invoice": has_invoice,
                "realization_ratio": round(
                    realization_ratio,
                    4,
                ),
                "risk_level": risk_level,
                "order_signal": signal,
                "read_only": True,
            }
        )

    return results


def summarize_order_behavior(
    orders: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(orders)

    realized = sum(
        1
        for order in orders
        if order["order_signal"] == "ORDER_REALIZED"
    )

    failed = sum(
        1
        for order in orders
        if order["order_signal"]
        == "ORDER_FAILURE_PRESSURE"
    )

    attempted = sum(
        1
        for order in orders
        if order["order_signal"]
        == "ORDER_PAYMENT_PENDING"
    )

    amount = round(
        sum(order["amount"] for order in orders),
        2,
    )

    paid = round(
        sum(order["amount_paid"] for order in orders),
        2,
    )

    return {
        "total_orders": total,
        "realized_orders": realized,
        "failed_orders": failed,
        "attempted_orders": attempted,
        "order_value": amount,
        "realized_value": paid,
        "realization_rate": round(
            paid / amount if amount > 0 else 0.0,
            4,
        ),
        "read_only": True,
    }
