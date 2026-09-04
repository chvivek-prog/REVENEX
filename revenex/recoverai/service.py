from __future__ import annotations

from typing import Any

from .ledger import (
    record_event,
    strategy_success_rate,
)
from .models import RecoveryAnalysis
from .predictor import predict_recovery
from .razorpay_client import (
    create_payment_link,
    fetch_payment,
)
from .strategy import decide_strategy
from .taxonomy import classify_failure


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def analyze_payment_failure(
    payment: dict[str, Any],
) -> RecoveryAnalysis:
    payment_id = str(
        payment.get("payment_id")
        or payment.get("id")
        or "unknown"
    )

    status = str(
        payment.get("status")
        or "failed"
    ).strip().lower()

    amount = _money(payment.get("amount"))

    attempts = int(
        payment.get("attempts")
        or payment.get("retry_count")
        or 0
    )

    if status == "pending":
        record_event(
            payment_id=payment_id,
            event_type="PAYMENT_PENDING",
            status=status,
            payload=payment,
            failure_type="pending",
            amount=amount,
            probability=1.0,
            strategy="POLL_STATUS",
        )

        return RecoveryAnalysis(
            payment_id=payment_id,
            status=status,
            failure_type="pending",
            failure_reason="Payment is unresolved.",
            amount=amount,
            recovery_probability=1.0,
            strategy="POLL_STATUS",
            rationale=(
                "Pending is not treated as a failure. "
                "Poll the payment API until a terminal state."
            ),
        )

    failure_type, reason = classify_failure(payment)

    historical_rate = strategy_success_rate(
        failure_type
    )

    probability = predict_recovery(
        failure_type,
        attempts=attempts,
        prior_success_rate=historical_rate,
    )

    strategy = decide_strategy(
        failure_type,
        probability,
        attempts=attempts,
    )

    record_event(
        payment_id=payment_id,
        event_type="PAYMENT_FAILED",
        status=status,
        payload=payment,
        failure_type=failure_type,
        amount=amount,
        probability=probability,
        strategy=strategy,
    )

    return RecoveryAnalysis(
        payment_id=payment_id,
        status=status,
        failure_type=failure_type,
        failure_reason=reason,
        amount=amount,
        recovery_probability=probability,
        strategy=strategy,
        rationale=(
            f"{failure_type}: {reason}. "
            f"Recovery probability is {probability:.0%}. "
            f"Recommended strategy: {strategy}."
        ),
    )


def poll_payment(payment_id: str):
    payment = fetch_payment(payment_id)
    status = str(
        payment.get("status")
        or "unknown"
    ).lower()

    record_event(
        payment_id=payment_id,
        event_type="PAYMENT_STATUS_POLLED",
        status=status,
        payload=payment,
        amount=_money(payment.get("amount")),
    )

    return {
        "payment_id": payment_id,
        "status": status,
        "terminal": status in {
            "captured",
            "failed",
            "refunded",
        },
        "payment": payment,
    }


def recover_payment(
    payment: dict[str, Any],
    *,
    human_approved: bool,
):
    analysis = analyze_payment_failure(payment)

    if analysis.strategy == "POLL_STATUS":
        return {
            "analysis": analysis.to_dict(),
            "action": "POLL_STATUS",
        }

    if not human_approved:
        return {
            "analysis": analysis.to_dict(),
            "action": "AWAITING_HUMAN_APPROVAL",
        }

    if analysis.strategy == "ESCALATE_OR_STOP":
        return {
            "analysis": analysis.to_dict(),
            "action": "ESCALATE_OR_STOP",
        }

    link = create_payment_link(
        amount=int(round(analysis.amount)),
        currency="INR",
        reference_id=f"recoverai-{analysis.payment_id}",
        description=(
            "RecoverAI recovery payment "
            f"for {analysis.payment_id}"
        ),
    )

    return {
        "analysis": analysis.to_dict(),
        "action": "PAYMENT_LINK_CREATED",
        "payment_link": link,
    }
