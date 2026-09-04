from __future__ import annotations


def decide_strategy(
    failure_type: str,
    probability: float,
    *,
    attempts: int = 0,
) -> str:
    if attempts >= 3:
        return "ESCALATE_OR_STOP"

    if failure_type == "bank_timeout":
        return (
            "SCHEDULED_RETRY"
            if probability >= 0.55
            else "RECOVERY_REVIEW"
        )

    if failure_type == "otp_timed_out":
        return (
            "NOTIFY_AND_DELAY"
            if probability >= 0.50
            else "RECOVERY_REVIEW"
        )

    if failure_type == "insufficient_funds":
        return "NOTIFY_AND_DELAY"

    if failure_type == "expired_card":
        return "REQUEST_METHOD_UPDATE"

    if failure_type == "transaction_limit":
        return "REQUEST_METHOD_UPDATE"

    if failure_type == "card_declined":
        return "RECOVERY_REVIEW"

    if failure_type == "gateway_error":
        return (
            "SCHEDULED_RETRY"
            if probability >= 0.50
            else "RECOVERY_REVIEW"
        )

    return "RECOVERY_REVIEW"
