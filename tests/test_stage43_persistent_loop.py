from revenex.loop.persistent_loop import (
    record_persistent_outcome,
    start_persistent_loop,
)
from revenex.persistence.outcome_store import OutcomeStore


def test_persistent_loop_creates_durable_outcome():
    store = OutcomeStore()

    result = start_persistent_loop(
        store,
        [
            {
                "customer_id": "customer-43",
                "amount": 200000,
                "outstanding_amount": 150000,
                "days_overdue": 90,
            }
        ],
        [],
        decision_id="decision-43",
        customer_id="customer-43",
    )

    stored = store.get_outcome(
        "decision-43"
    )

    assert result.decision_id == "decision-43"
    assert stored is not None
    assert stored.expected_collection == (
        result.decision.expected_collection
    )

    store.close()


def test_persistent_loop_survives_reopen(tmp_path):
    database = tmp_path / "persistent-loop.db"

    store = OutcomeStore(database)

    result = start_persistent_loop(
        store,
        [
            {
                "customer_id": "customer-43",
                "amount": 100000,
                "outstanding_amount": 80000,
                "days_overdue": 60,
            }
        ],
        [],
        decision_id="persistent-decision",
        customer_id="customer-43",
    )

    store.close()

    reopened = OutcomeStore(database)

    stored = reopened.get_outcome(
        result.decision_id
    )

    assert stored is not None
    assert stored.decision_id == "persistent-decision"

    reopened.close()


def test_persistent_outcome_creates_learning_signal():
    store = OutcomeStore()

    result = start_persistent_loop(
        store,
        [
            {
                "customer_id": "customer-43",
                "amount": 100000,
                "outstanding_amount": 80000,
                "days_overdue": 60,
            }
        ],
        [],
        decision_id="learning-decision",
    )

    updated = record_persistent_outcome(
        store,
        result,
        actual_collection=50000,
        actual_remaining_exposure=30000,
    )

    signals = store.list_learning_signals(
        "learning-decision"
    )

    assert updated.stored_outcome.actual_collection == 50000
    assert len(signals) == 1
    assert signals[0]["decision_id"] == (
        "learning-decision"
    )

    store.close()


def test_persistent_loop_is_never_executable():
    store = OutcomeStore()

    result = start_persistent_loop(
        store,
        [
            {
                "customer_id": "customer-43",
                "amount": 500000,
                "outstanding_amount": 400000,
                "days_overdue": 120,
            }
        ],
        [],
        decision_id="safety-decision",
    )

    updated = record_persistent_outcome(
        store,
        result,
        actual_collection=200000,
        actual_remaining_exposure=200000,
    )

    assert updated.execution_allowed is False
    assert updated.automatic_action is False
    assert updated.financial_mutation is False
    assert updated.provider_mutation is False

    store.close()


def test_duplicate_start_reuses_persistent_outcome():
    store = OutcomeStore()

    first = start_persistent_loop(
        store,
        [
            {
                "customer_id": "customer-43",
                "amount": 100000,
                "outstanding_amount": 50000,
                "days_overdue": 45,
            }
        ],
        [],
        decision_id="idempotent-decision",
    )

    second = start_persistent_loop(
        store,
        [
            {
                "customer_id": "customer-43",
                "amount": 100000,
                "outstanding_amount": 50000,
                "days_overdue": 45,
            }
        ],
        [],
        decision_id="idempotent-decision",
    )

    assert (
        first.stored_outcome.id
        == second.stored_outcome.id
    )

    store.close()
