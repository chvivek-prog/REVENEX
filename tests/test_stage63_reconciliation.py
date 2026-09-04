
from revenex.reconciliation import (
    ReconciliationSeverity,
    ReconciliationStatus,
    ReconciliationStore,
    build_exception_queue,
    reconcile_batch,
    reconcile_record,
    summarize_ledger_exposure,
)


def test_matching_three_way_reconciliation():

    record = reconcile_record(
        reconciliation_id="rec-1",
        resource_type="payment",
        resource_id="pay-1",
        expected_amount=10000,
        observed_amount=10000,
        internal_amount=10000,
        expected_status="CAPTURED",
        observed_status="CAPTURED",
        internal_status="CAPTURED",
    )

    assert (
        record.status
        == ReconciliationStatus.MATCHED
    )

    assert record.revenue_impact == 0
    assert record.requires_human_review is False


def test_amount_mismatch():

    record = reconcile_record(
        reconciliation_id="rec-2",
        resource_type="payment",
        resource_id="pay-2",
        expected_amount=10000,
        observed_amount=9500,
        internal_amount=10000,
        expected_status="CAPTURED",
        observed_status="CAPTURED",
        internal_status="CAPTURED",
    )

    assert (
        record.status
        == ReconciliationStatus.PARTIAL_MATCH
    )

    assert record.amount_variance == 500
    assert record.revenue_impact == 500
    assert record.requires_human_review is True


def test_large_mismatch_is_high_severity():

    record = reconcile_record(
        reconciliation_id="rec-3",
        resource_type="payment",
        resource_id="pay-3",
        expected_amount=500000,
        observed_amount=300000,
        internal_amount=500000,
        expected_status="CAPTURED",
        observed_status="CAPTURED",
        internal_status="CAPTURED",
    )

    assert (
        record.severity
        == ReconciliationSeverity.HIGH
    )

    assert record.revenue_impact == 200000


def test_critical_mismatch():

    record = reconcile_record(
        reconciliation_id="rec-4",
        resource_type="settlement",
        resource_id="set-1",
        expected_amount=1000000,
        observed_amount=400000,
        internal_amount=1000000,
        expected_status="PROCESSED",
        observed_status="PROCESSED",
        internal_status="PROCESSED",
    )

    assert (
        record.severity
        == ReconciliationSeverity.CRITICAL
    )


def test_missing_observed_state():

    record = reconcile_record(
        reconciliation_id="rec-5",
        resource_type="payment",
        resource_id="pay-5",
        expected_amount=50000,
        observed_amount=None,
        internal_amount=50000,
        expected_status="CAPTURED",
        observed_status=None,
        internal_status="CAPTURED",
    )

    assert (
        record.status
        == ReconciliationStatus.MISSING_OBSERVED
    )

    assert record.requires_human_review is True


def test_missing_internal_state():

    record = reconcile_record(
        reconciliation_id="rec-6",
        resource_type="payment",
        resource_id="pay-6",
        expected_amount=50000,
        observed_amount=50000,
        internal_amount=None,
        expected_status="CAPTURED",
        observed_status="CAPTURED",
        internal_status=None,
    )

    assert (
        record.status
        == ReconciliationStatus.MISSING_INTERNAL
    )


def test_status_mismatch():

    record = reconcile_record(
        reconciliation_id="rec-7",
        resource_type="payment",
        resource_id="pay-7",
        expected_amount=50000,
        observed_amount=50000,
        internal_amount=50000,
        expected_status="CAPTURED",
        observed_status="FAILED",
        internal_status="CAPTURED",
    )

    assert record.requires_human_review is True
    assert record.revenue_impact == 0


def test_batch_reconciliation():

    report = reconcile_batch(
        [
            {
                "reconciliation_id": "a",
                "resource_type": "payment",
                "resource_id": "p1",
                "expected_amount": 100,
                "observed_amount": 100,
                "internal_amount": 100,
            },
            {
                "reconciliation_id": "b",
                "resource_type": "payment",
                "resource_id": "p2",
                "expected_amount": 200,
                "observed_amount": 150,
                "internal_amount": 200,
            },
        ]
    )

    assert report.total_records == 2
    assert report.matched_records == 1
    assert report.partial_records == 1
    assert report.total_revenue_impact == 50


def test_exception_queue():

    report = reconcile_batch(
        [
            {
                "reconciliation_id": "a",
                "resource_type": "payment",
                "resource_id": "p1",
                "expected_amount": 100,
                "observed_amount": 50,
                "internal_amount": 100,
            },
            {
                "reconciliation_id": "b",
                "resource_type": "payment",
                "resource_id": "p2",
                "expected_amount": 100,
                "observed_amount": 100,
                "internal_amount": 100,
            },
        ]
    )

    queue = build_exception_queue(report)

    assert len(queue) == 1
    assert queue[0]["resource_id"] == "p1"


def test_ledger_summary():

    report = reconcile_batch(
        [
            {
                "reconciliation_id": "a",
                "resource_type": "payment",
                "resource_id": "p1",
                "expected_amount": 100,
                "observed_amount": 90,
                "internal_amount": 100,
            },
        ]
    )

    summary = summarize_ledger_exposure(
        report
    )

    assert summary["revenue_impact"] == 10
    assert summary["requires_human_review"] is True
    assert summary["automatic_correction"] is False
    assert summary["financial_mutation"] is False


def test_reconciliation_store():

    store = ReconciliationStore()

    record = reconcile_record(
        reconciliation_id="persist-1",
        resource_type="settlement",
        resource_id="set-1",
        expected_amount=1000,
        observed_amount=900,
        internal_amount=1000,
    )

    assert store.save(record) is True
    assert store.save(record) is False

    stored = store.get(
        "persist-1"
    )

    assert stored is not None
    assert stored["revenue_impact"] == 100
    assert stored["requires_human_review"] is True

    assert len(store.list()) == 1

    store.close()


def test_safety_boundary():

    report = reconcile_batch([])

    assert (
        report.safety["execution_allowed"]
        is False
    )

    assert (
        report.safety["automatic_action"]
        is False
    )

    assert (
        report.safety["financial_mutation"]
        is False
    )

    assert (
        report.safety["provider_mutation"]
        is False
    )

    assert (
        report.safety["human_approval_required"]
        is True
    )

    assert report.safety["read_only"] is True
