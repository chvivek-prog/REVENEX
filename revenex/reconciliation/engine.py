
from __future__ import annotations

from typing import Any

from revenex.reconciliation.contracts import (
    MismatchType,
    ReconciliationRecord,
    ReconciliationReport,
    ReconciliationSeverity,
    ReconciliationStatus,
)


SAFETY = {
    "execution_allowed": False,
    "automatic_action": False,
    "financial_mutation": False,
    "provider_mutation": False,
    "human_approval_required": True,
    "read_only": True,
}


def _number(
    value: Any,
) -> float | None:

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _status(
    value: Any,
) -> str | None:

    if value is None:
        return None

    return str(value).upper()


def _severity(
    revenue_impact: float,
    mismatch_type: MismatchType,
) -> ReconciliationSeverity:

    impact = abs(float(revenue_impact))

    if mismatch_type == MismatchType.NONE:
        return ReconciliationSeverity.NONE

    if impact >= 500000:
        return ReconciliationSeverity.CRITICAL

    if impact >= 100000:
        return ReconciliationSeverity.HIGH

    if impact >= 10000:
        return ReconciliationSeverity.MEDIUM

    return ReconciliationSeverity.LOW


def reconcile_record(
    *,
    reconciliation_id: str,
    resource_type: str,
    resource_id: str,
    expected_amount: float | None = None,
    observed_amount: float | None = None,
    internal_amount: float | None = None,
    expected_status: str | None = None,
    observed_status: str | None = None,
    internal_status: str | None = None,
    tolerance: float = 0.01,
) -> ReconciliationRecord:

    expected_amount = _number(expected_amount)
    observed_amount = _number(observed_amount)
    internal_amount = _number(internal_amount)

    expected_status = _status(expected_status)
    observed_status = _status(observed_status)
    internal_status = _status(internal_status)

    evidence: list[str] = []

    # --------------------------------------------------------
    # DATA COMPLETENESS
    # --------------------------------------------------------

    missing_expected = (
        expected_amount is None
        and expected_status is None
    )

    missing_observed = (
        observed_amount is None
        and observed_status is None
    )

    missing_internal = (
        internal_amount is None
        and internal_status is None
    )

    if (
        missing_expected
        and missing_observed
        and missing_internal
    ):
        return ReconciliationRecord(
            reconciliation_id=reconciliation_id,
            resource_type=resource_type,
            resource_id=resource_id,
            expected_amount=None,
            observed_amount=None,
            internal_amount=None,
            expected_status=None,
            observed_status=None,
            internal_status=None,
            status=ReconciliationStatus.INSUFFICIENT_DATA,
            mismatch_type=MismatchType.UNKNOWN,
            amount_variance=None,
            revenue_impact=0.0,
            severity=ReconciliationSeverity.NONE,
            explanation="No reconciliation evidence was supplied.",
            requires_human_review=False,
            evidence=(
                "Expected, observed, and internal state are missing.",
            ),
        )

    if missing_expected:
        return ReconciliationRecord(
            reconciliation_id=reconciliation_id,
            resource_type=resource_type,
            resource_id=resource_id,
            expected_amount=expected_amount,
            observed_amount=observed_amount,
            internal_amount=internal_amount,
            expected_status=expected_status,
            observed_status=observed_status,
            internal_status=internal_status,
            status=ReconciliationStatus.MISSING_EXPECTED,
            mismatch_type=MismatchType.MISSING_EVENT,
            amount_variance=None,
            revenue_impact=abs(
                observed_amount or internal_amount or 0.0
            ),
            severity=ReconciliationSeverity.MEDIUM,
            explanation="Expected state is missing.",
            requires_human_review=True,
            evidence=(
                "Expected state was not supplied.",
            ),
        )

    if missing_observed:
        impact = abs(
            expected_amount or internal_amount or 0.0
        )

        severity = _severity(
            impact,
            MismatchType.MISSING_EVENT,
        )

        return ReconciliationRecord(
            reconciliation_id=reconciliation_id,
            resource_type=resource_type,
            resource_id=resource_id,
            expected_amount=expected_amount,
            observed_amount=None,
            internal_amount=internal_amount,
            expected_status=expected_status,
            observed_status=None,
            internal_status=internal_status,
            status=ReconciliationStatus.MISSING_OBSERVED,
            mismatch_type=MismatchType.MISSING_EVENT,
            amount_variance=None,
            revenue_impact=impact,
            severity=severity,
            explanation=(
                "Expected/internal state exists but "
                "no provider observation was supplied."
            ),
            requires_human_review=True,
            evidence=(
                "Observed provider state is missing.",
            ),
        )

    if missing_internal:
        impact = abs(
            expected_amount or observed_amount or 0.0
        )

        severity = _severity(
            impact,
            MismatchType.MISSING_EVENT,
        )

        return ReconciliationRecord(
            reconciliation_id=reconciliation_id,
            resource_type=resource_type,
            resource_id=resource_id,
            expected_amount=expected_amount,
            observed_amount=observed_amount,
            internal_amount=None,
            expected_status=expected_status,
            observed_status=observed_status,
            internal_status=None,
            status=ReconciliationStatus.MISSING_INTERNAL,
            mismatch_type=MismatchType.MISSING_EVENT,
            amount_variance=None,
            revenue_impact=impact,
            severity=severity,
            explanation=(
                "Expected/provider state exists but "
                "internal state is missing."
            ),
            requires_human_review=True,
            evidence=(
                "Internal state is missing.",
            ),
        )

    # --------------------------------------------------------
    # AMOUNT COMPARISON
    # --------------------------------------------------------

    values = [
        expected_amount,
        observed_amount,
        internal_amount,
    ]

    maximum = max(values)
    minimum = min(values)

    amount_variance = maximum - minimum

    amount_match = (
        amount_variance <= tolerance
    )

    if not amount_match:
        mismatch_type = (
            MismatchType.AMOUNT_MISMATCH
        )

        revenue_impact = amount_variance

        evidence.extend([
            f"expected_amount={expected_amount:.2f}",
            f"observed_amount={observed_amount:.2f}",
            f"internal_amount={internal_amount:.2f}",
            f"amount_variance={amount_variance:.2f}",
        ])

    else:
        mismatch_type = MismatchType.NONE
        revenue_impact = 0.0

    # --------------------------------------------------------
    # STATUS COMPARISON
    # --------------------------------------------------------

    statuses = [
        expected_status,
        observed_status,
        internal_status,
    ]

    known_statuses = {
        value
        for value in statuses
        if value is not None
    }

    status_match = (
        len(known_statuses) <= 1
    )

    if not status_match and mismatch_type == MismatchType.NONE:
        mismatch_type = (
            MismatchType.STATUS_MISMATCH
        )

        evidence.extend([
            f"expected_status={expected_status}",
            f"observed_status={observed_status}",
            f"internal_status={internal_status}",
        ])

    # --------------------------------------------------------
    # FINAL CLASSIFICATION
    # --------------------------------------------------------

    if amount_match and status_match:

        status = ReconciliationStatus.MATCHED
        severity = ReconciliationSeverity.NONE
        explanation = (
            "Expected, observed, and internal state "
            "are aligned."
        )
        requires_review = False

    elif amount_match or status_match:

        status = ReconciliationStatus.PARTIAL_MATCH
        severity = _severity(
            revenue_impact,
            mismatch_type,
        )
        explanation = (
            "Some reconciliation dimensions match "
            "while others require investigation."
        )
        requires_review = True

    else:

        status = ReconciliationStatus.MISMATCH
        severity = _severity(
            revenue_impact,
            mismatch_type,
        )
        explanation = (
            "Expected, observed, and internal state "
            "contain a material mismatch."
        )
        requires_review = True

    return ReconciliationRecord(
        reconciliation_id=reconciliation_id,
        resource_type=resource_type,
        resource_id=resource_id,
        expected_amount=expected_amount,
        observed_amount=observed_amount,
        internal_amount=internal_amount,
        expected_status=expected_status,
        observed_status=observed_status,
        internal_status=internal_status,
        status=status,
        mismatch_type=mismatch_type,
        amount_variance=(
            amount_variance
            if not amount_match
            else 0.0
        ),
        revenue_impact=revenue_impact,
        severity=severity,
        explanation=explanation,
        requires_human_review=requires_review,
        evidence=tuple(evidence),
    )


def reconcile_batch(
    records: list[dict[str, Any]],
    *,
    tolerance: float = 0.01,
) -> ReconciliationReport:

    results = []

    for item in records:

        results.append(
            reconcile_record(
                reconciliation_id=str(
                    item["reconciliation_id"]
                ),
                resource_type=str(
                    item["resource_type"]
                ),
                resource_id=str(
                    item["resource_id"]
                ),
                expected_amount=item.get(
                    "expected_amount"
                ),
                observed_amount=item.get(
                    "observed_amount"
                ),
                internal_amount=item.get(
                    "internal_amount"
                ),
                expected_status=item.get(
                    "expected_status"
                ),
                observed_status=item.get(
                    "observed_status"
                ),
                internal_status=item.get(
                    "internal_status"
                ),
                tolerance=tolerance,
            )
        )

    matched = sum(
        r.status == ReconciliationStatus.MATCHED
        for r in results
    )

    partial = sum(
        r.status == ReconciliationStatus.PARTIAL_MATCH
        for r in results
    )

    mismatched = sum(
        r.status == ReconciliationStatus.MISMATCH
        for r in results
    )

    missing = sum(
        r.status
        in {
            ReconciliationStatus.MISSING_EXPECTED,
            ReconciliationStatus.MISSING_OBSERVED,
            ReconciliationStatus.MISSING_INTERNAL,
        }
        for r in results
    )

    critical = sum(
        r.severity
        == ReconciliationSeverity.CRITICAL
        for r in results
    )

    high = sum(
        r.severity
        == ReconciliationSeverity.HIGH
        for r in results
    )

    total_impact = sum(
        r.revenue_impact
        for r in results
    )

    if not results:
        overall = (
            ReconciliationStatus.INSUFFICIENT_DATA
        )

    elif mismatched or missing:
        overall = ReconciliationStatus.MISMATCH

    elif partial:
        overall = (
            ReconciliationStatus.PARTIAL_MATCH
        )

    else:
        overall = ReconciliationStatus.MATCHED

    summary = (
        f"{len(results)} reconciliation record(s): "
        f"{matched} matched, "
        f"{partial} partial, "
        f"{mismatched} mismatched, "
        f"{missing} missing. "
        f"Revenue impact="
        f"₹{total_impact:,.2f}. "
        f"Human review required for exceptions."
    )

    return ReconciliationReport(
        status=overall,
        total_records=len(results),
        matched_records=matched,
        partial_records=partial,
        mismatched_records=mismatched,
        missing_records=missing,
        critical_records=critical,
        high_records=high,
        total_revenue_impact=total_impact,
        records=tuple(results),
        executive_summary=summary,
        safety=dict(SAFETY),
    )




# ============================================================
# LEGACY COMPATIBILITY LAYER
# ============================================================
#
# Preserves the Stage 58 public contract while Phase 13 uses
# the richer three-way reconciliation engine internally.
#
# IMPORTANT:
# Legacy reconcile() is intentionally TWO-WAY when no
# internal_amount is supplied:
#
#     expected ↔ observed
#
# It must NOT become MISSING_INTERNAL merely because the
# optional Phase 13 internal ledger value is absent.
# ============================================================


def reconcile(
    *,
    entity_type=None,
    entity_id=None,
    expected_amount=None,
    observed_amount=None,
    internal_amount=None,
    tolerance=0.01,
    **kwargs,
):
    """
    Legacy Stage 58 reconciliation contract.

    Two-way mode:
        expected_amount ↔ observed_amount

    Three-way mode:
        expected_amount ↔ observed_amount ↔ internal_amount

    Always read-only.
    """

    entity_type = (
        entity_type
        if entity_type is not None
        else kwargs.pop(
            "resource_type",
            "unknown",
        )
    )

    entity_id = (
        entity_id
        if entity_id is not None
        else kwargs.pop(
            "resource_id",
            "unknown",
        )
    )

    # --------------------------------------------------------
    # Legacy two-way reconciliation
    # --------------------------------------------------------

    if internal_amount is None:

        expected = (
            0.0
            if expected_amount is None
            else float(expected_amount)
        )

        observed = (
            0.0
            if observed_amount is None
            else float(observed_amount)
        )

        variance = observed - expected

        if abs(variance) <= tolerance:
            status = "RECONCILED"
        elif variance < 0:
            status = "VARIANCE_UNDER"
        else:
            status = "VARIANCE_OVER"

        # Small compatibility object with the exact Stage 58
        # contract. Keep it deliberately immutable.
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class LegacyReconciliationResult:
            entity_type: str
            entity_id: str
            expected_amount: float
            observed_amount: float
            variance: float
            status: str
            confidence: float
            read_only: bool = True
            financial_mutation: bool = False
            provider_mutation: bool = False
            execution_allowed: bool = False
            automatic_action: bool = False

        return LegacyReconciliationResult(
            entity_type=str(entity_type),
            entity_id=str(entity_id),
            expected_amount=expected,
            observed_amount=observed,
            variance=variance,
            status=status,
            confidence=(
                1.0
                if expected == observed
                else max(
                    0.0,
                    1.0
                    - abs(variance)
                    / max(abs(expected), 1.0),
                )
            ),
        )

    # --------------------------------------------------------
    # Phase 13 three-way reconciliation
    # --------------------------------------------------------

    result = reconcile_record(
        reconciliation_id=(
            f"{entity_type}-{entity_id}"
        ),
        resource_type=str(entity_type),
        resource_id=str(entity_id),
        expected_amount=expected_amount,
        observed_amount=observed_amount,
        internal_amount=internal_amount,
        tolerance=tolerance,
    )

    return result


def reconcile_payments(
    expected_payments,
    observed_payments,
    internal_payments=None,
    *,
    tolerance=0.01,
):
    """
    Legacy payment collection API.

    Returns one result per payment.
    """

    expected_payments = expected_payments or []
    observed_payments = observed_payments or []

    internal_payments = (
        internal_payments or []
    )

    def index(items):

        result = {}

        for item in items:

            if not isinstance(item, dict):
                continue

            key = (
                item.get("payment_id")
                or item.get("id")
                or item.get("transaction_id")
                or item.get("order_id")
            )

            if key is not None:
                result[str(key)] = item

        return result

    expected = index(
        expected_payments
    )

    observed = index(
        observed_payments
    )

    internal = index(
        internal_payments
    )

    keys = (
        set(expected)
        | set(observed)
        | set(internal)
    )

    results = []

    for key in sorted(keys):

        e = expected.get(key)
        o = observed.get(key)
        i = internal.get(key)

        def amount(item):

            if not isinstance(item, dict):
                return None

            for field in (
                "amount",
                "amount_paid",
                "amount_captured",
                "value",
                "total",
            ):
                if field in item:
                    return item[field]

            return None

        # IMPORTANT:
        # If no internal payment collection is supplied,
        # use the legacy two-way API.
        internal_amount = (
            amount(i)
            if i is not None
            else None
        )

        results.append(
            reconcile(
                entity_type="payment",
                entity_id=str(key),
                expected_amount=amount(e),
                observed_amount=amount(o),
                internal_amount=internal_amount,
                tolerance=tolerance,
            )
        )

    return results


def summarize_reconciliation(
    results,
):
    """
    Legacy Stage 58 summary contract.
    """

    results = (
        []
        if results is None
        else list(results)
    )

    total_items = len(results)

    reconciled = 0
    variance_under = 0
    variance_over = 0
    mismatched = 0
    total_variance = 0.0

    for result in results:

        status = getattr(
            result,
            "status",
            "",
        )

        status_value = (
            status.value
            if hasattr(status, "value")
            else str(status)
        ).upper()

        if status_value == "RECONCILED":
            reconciled += 1

        elif status_value == "VARIANCE_UNDER":
            variance_under += 1
            mismatched += 1

        elif status_value == "VARIANCE_OVER":
            variance_over += 1
            mismatched += 1

        else:
            mismatched += 1

        variance = getattr(
            result,
            "variance",
            0.0,
        )

        try:
            total_variance += float(
                variance or 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

    return {
        # Exact Stage 58 contract.
        "total_items": total_items,
        "reconciled_items": reconciled,
        "variance_under_items":
            variance_under,
        "variance_over_items":
            variance_over,
        "mismatched_items":
            mismatched,
        "total_variance":
            total_variance,

        # Additional compatibility fields.
        "total": total_items,
        "matched": reconciled,
        "mismatched": mismatched,
        "missing": 0,
        "variance": total_variance,

        # Safety contract.
        "read_only": True,
        "requires_human_review":
            mismatched > 0,
        "human_review_required":
            mismatched > 0,
        "execution_allowed": False,
        "automatic_action": False,
        "financial_mutation": False,
        "provider_mutation": False,
        "human_approval_required": True,
    }
