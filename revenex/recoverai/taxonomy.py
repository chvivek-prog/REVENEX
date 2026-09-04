from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip().lower()


def classify_failure(
    payment: dict[str, Any],
) -> tuple[str, str]:
    code = _text(payment.get("error_code"))
    reason = _text(
        payment.get("error_reason")
        or payment.get("error_description")
        or payment.get("description")
    )
    step = _text(payment.get("error_step"))
    source = _text(payment.get("error_source"))

    text = " ".join((code, reason, step, source))

    if any(x in text for x in ("expired_card", "expired card", "expired")):
        return "expired_card", reason or code or "expired card"

    if any(x in text for x in (
        "insufficient_funds",
        "insufficient funds",
        "insufficient",
        "balance",
    )):
        return "insufficient_funds", reason or code or "insufficient funds"

    if any(x in text for x in (
        "otp",
        "one time password",
        "authentication timeout",
        "otp_timed_out",
    )):
        return "otp_timed_out", reason or code or "OTP timed out"

    if any(x in text for x in (
        "transaction_limit",
        "transaction limit",
        "limit exceeded",
    )):
        return "transaction_limit", reason or code or "transaction limit"

    if "declin" in text or "card_declined" in text:
        return "card_declined", reason or code or "card declined"

    if any(x in text for x in (
        "gateway",
        "processor",
    )):
        return "gateway_error", reason or code or "gateway error"

    if source in {"bank", "issuer"} or any(
        x in text for x in (
            "bank timeout",
            "bank_timeout",
            "issuer timeout",
            "timed out",
            "timeout",
        )
    ):
        return "bank_timeout", reason or code or "bank timeout"

    return "unknown", reason or code or "unknown failure"
