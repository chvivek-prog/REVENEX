
from __future__ import annotations

from typing import Any

from revenex.events.contracts import (
    NormalizedEvent,
    ProviderEvent,
)


_RESOURCE_MAP = {
    "payment": "payment",
    "payment.captured": "payment",
    "payment.failed": "payment",
    "invoice": "invoice",
    "invoice.paid": "invoice",
    "order": "order",
    "subscription": "subscription",
    "subscription.activated": "subscription",
    "subscription.cancelled": "subscription",
    "refund": "refund",
    "settlement": "settlement",
    "dispute": "dispute",
    "payout": "payout",
}


def _resource_type(
    event_type: str,
) -> str | None:

    if event_type in _RESOURCE_MAP:
        return _RESOURCE_MAP[event_type]

    prefix = event_type.split(".", 1)[0]

    return _RESOURCE_MAP.get(prefix)


def _resource_id(
    payload: dict[str, Any],
) -> str | None:

    for key in (
        "resource_id",
        "id",
        "payment_id",
        "invoice_id",
        "order_id",
        "subscription_id",
        "refund_id",
        "settlement_id",
        "dispute_id",
        "payout_id",
    ):
        value = payload.get(key)

        if value is not None:
            return str(value)

    entity = payload.get("entity")

    if isinstance(entity, dict):
        value = entity.get("id")

        if value is not None:
            return str(value)

    return None


def normalize_event(
    event: ProviderEvent,
) -> NormalizedEvent:

    resource = _resource_type(
        event.event_type
    )

    resource_id = _resource_id(
        event.payload
    )

    action = (
        event.event_type
        .split(".", 1)[1]
        if "." in event.event_type
        else event.event_type
    )

    return NormalizedEvent(
        event_id=event.event_id,
        provider=event.provider,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        resource_type=resource,
        resource_id=resource_id,
        action=action,
        payload=dict(event.payload),
        sandbox=event.sandbox,
    )
