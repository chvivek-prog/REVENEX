from __future__ import annotations


BASE_PROBABILITY = {
    "bank_timeout": 0.75,
    "otp_timed_out": 0.65,
    "insufficient_funds": 0.35,
    "expired_card": 0.10,
    "card_declined": 0.30,
    "gateway_error": 0.55,
    "transaction_limit": 0.25,
    "unknown": 0.20,
}


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def predict_recovery(
    failure_type: str,
    *,
    attempts: int = 0,
    prior_success_rate: float | None = None,
) -> float:
    probability = BASE_PROBABILITY.get(
        failure_type,
        BASE_PROBABILITY["unknown"],
    )

    if prior_success_rate is not None:
        probability = (
            0.70 * probability
            + 0.30 * _clip(float(prior_success_rate))
        )

    if attempts >= 2:
        probability -= min(
            0.20,
            0.05 * (attempts - 1),
        )

    return round(_clip(probability), 4)
