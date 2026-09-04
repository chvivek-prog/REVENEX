from pathlib import Path

from revenex.recoverai import (
    analyze_payment_failure,
)
from revenex.recoverai.predictor import (
    predict_recovery,
)
from revenex.recoverai.strategy import (
    decide_strategy,
)
from revenex.recoverai.taxonomy import (
    classify_failure,
)


def test_bank_timeout_classification():
    failure_type, reason = classify_failure(
        {
            "error_reason": "bank timeout",
            "error_source": "bank",
        }
    )

    assert failure_type == "bank_timeout"
    assert reason == "bank timeout"


def test_bank_timeout_prediction():
    assert predict_recovery(
        "bank_timeout"
    ) == 0.75


def test_bank_timeout_strategy():
    assert decide_strategy(
        "bank_timeout",
        0.75,
    ) == "SCHEDULED_RETRY"


def test_pending_is_not_failed():
    result = analyze_payment_failure(
        {
            "id": "pay_pending_test",
            "amount": 100000,
            "status": "pending",
        }
    )

    assert result.failure_type == "pending"
    assert result.strategy == "POLL_STATUS"
    assert result.read_only is True
    assert result.requires_human_approval is True
    assert result.automatic_action is False
    assert result.financial_mutation is False


def test_failed_payment_is_recovery_candidate():
    result = analyze_payment_failure(
        {
            "id": "pay_failed_test",
            "amount": 100000,
            "status": "failed",
            "error_reason": "bank timeout",
            "error_source": "bank",
        }
    )

    assert result.failure_type == "bank_timeout"
    assert result.recovery_probability == 0.75
    assert result.strategy == "SCHEDULED_RETRY"
    assert result.read_only is True
