
from __future__ import annotations

import json
import os

from revenex.recoverai.service import analyze_payment_failure
from revenex.webhooks.validation import verify_webhook_signature


def handle_recoverai_webhook(
    raw_body: bytes,
    signature: str | None,
):
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    if not secret:
        raise RuntimeError(
            "RAZORPAY_WEBHOOK_SECRET is required."
        )

    if not signature:
        raise PermissionError(
            "X-Razorpay-Signature is required."
        )

    if not verify_webhook_signature(
        raw_body,
        signature,
        secret,
    ):
        raise PermissionError(
            "Invalid Razorpay webhook signature."
        )

    payload = json.loads(raw_body.decode("utf-8"))

    event = payload.get("event")

    if event == "payment.failed":
        payment = (
            payload
            .get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        return {
            "event": event,
            "handled": True,
            "analysis": analyze_payment_failure(payment),
        }

    if event == "payment_link.paid":
        payment_link = (
            payload
            .get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
        )

        return {
            "event": event,
            "handled": True,
            "outcome": {
                "status": "RECOVERED",
                "payment_link_id": payment_link.get("id"),
                "amount": payment_link.get("amount"),
            },
        }

    return {
        "event": event,
        "handled": False,
    }
