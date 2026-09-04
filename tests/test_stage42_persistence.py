from revenex.persistence.outcome_store import OutcomeStore


def test_create_pending_outcome():
    store = OutcomeStore()

    outcome = store.create_outcome(
        decision_id="d42",
        customer_id="customer-42",
        expected_collection=60000,
        expected_remaining_exposure=40000,
    )

    assert outcome.decision_id == "d42"
    assert outcome.customer_id == "customer-42"
    assert outcome.expected_collection == 60000
    assert outcome.actual_collection is None
    assert outcome.status == "PENDING"

    store.close()


def test_outcome_survives_store_reopen(tmp_path):
    database = tmp_path / "revenex.db"

    store = OutcomeStore(database)

    store.create_outcome(
        decision_id="persistent-1",
        customer_id="customer-1",
        expected_collection=50000,
        expected_remaining_exposure=30000,
    )

    store.close()

    reopened = OutcomeStore(database)

    outcome = reopened.get_outcome(
        "persistent-1"
    )

    assert outcome is not None
    assert outcome.expected_collection == 50000
    assert outcome.expected_remaining_exposure == 30000

    reopened.close()


def test_duplicate_decision_does_not_create_duplicate():
    store = OutcomeStore()

    first = store.create_outcome(
        decision_id="duplicate-1",
        customer_id="customer-1",
        expected_collection=10000,
        expected_remaining_exposure=5000,
    )

    second = store.create_outcome(
        decision_id="duplicate-1",
        customer_id="customer-1",
        expected_collection=99999,
        expected_remaining_exposure=99999,
    )

    assert first.id == second.id
    assert second.expected_collection == 10000
    assert second.expected_remaining_exposure == 5000

    store.close()


def test_record_observed_outcome():
    store = OutcomeStore()

    store.create_outcome(
        decision_id="observed-1",
        customer_id="customer-1",
        expected_collection=50000,
        expected_remaining_exposure=50000,
    )

    outcome = store.record_outcome(
        decision_id="observed-1",
        actual_collection=45000,
        actual_remaining_exposure=55000,
    )

    assert outcome.actual_collection == 45000
    assert outcome.actual_remaining_exposure == 55000
    assert outcome.status == "OBSERVED"

    store.close()


def test_negative_values_are_normalized():
    store = OutcomeStore()

    store.create_outcome(
        decision_id="safe-1",
        customer_id="customer-1",
        expected_collection=10000,
        expected_remaining_exposure=10000,
    )

    outcome = store.record_outcome(
        decision_id="safe-1",
        actual_collection=-500,
        actual_remaining_exposure=-1000,
    )

    assert outcome.actual_collection == 0
    assert outcome.actual_remaining_exposure == 0

    store.close()


def test_unknown_decision_cannot_receive_outcome():
    store = OutcomeStore()

    try:
        store.record_outcome(
            decision_id="does-not-exist",
            actual_collection=100,
            actual_remaining_exposure=0,
        )
    except KeyError:
        pass
    else:
        raise AssertionError(
            "Unknown decision should raise KeyError."
        )

    store.close()


def test_evaluation_and_learning_signal_are_persisted():
    store = OutcomeStore()

    store.create_outcome(
        decision_id="learn-1",
        customer_id="customer-1",
        expected_collection=60000,
        expected_remaining_exposure=40000,
    )

    evaluation_id = store.record_evaluation(
        decision_id="learn-1",
        status="SUCCESS",
        collection_variance=-2000,
        collection_accuracy=0.9666,
        exposure_variance=2000,
        learning_signal="PREDICTION_ALIGNED",
    )

    signal_id = store.record_learning_signal(
        decision_id="learn-1",
        signal="PREDICTION_ALIGNED",
        strength=0.0334,
        evidence="prediction aligned with observed collection",
    )

    assert evaluation_id > 0
    assert signal_id > 0

    signals = store.list_learning_signals(
        "learn-1"
    )

    assert len(signals) == 1
    assert signals[0]["signal"] == "PREDICTION_ALIGNED"

    store.close()
