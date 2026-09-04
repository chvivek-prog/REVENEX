from __future__ import annotations

from typing import Any

from .contracts import (
    LeakageSeverity,
    LeakageType,
    RevenueLeakage,
    RevenueLeakageReport,
)


def _money(value: Any) -> float:
    try:
        return max(float(value), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _severity(
    amount: float,
    expected: float,
) -> LeakageSeverity:
    if amount <= 0:
        return LeakageSeverity.LOW

    ratio = (
        amount / expected
        if expected > 0
        else 1.0
    )

    if ratio >= 0.75 or amount >= 100000:
        return LeakageSeverity.CRITICAL

    if ratio >= 0.40 or amount >= 50000:
        return LeakageSeverity.HIGH

    if ratio >= 0.10 or amount >= 10000:
        return LeakageSeverity.MEDIUM

    return LeakageSeverity.LOW


def _leakage(
    *,
    leakage_type: LeakageType,
    entity_type: str,
    entity_id: str,
    expected: float,
    observed: float,
    explanation: str,
    evidence: tuple[str, ...],
) -> RevenueLeakage:

    amount = max(
        expected - observed,
        0.0,
    )

    return RevenueLeakage(
        leakage_id=(
            f"{leakage_type.value}:"
            f"{entity_type}:"
            f"{entity_id}"
        ),
        leakage_type=leakage_type,
        severity=_severity(
            amount,
            expected,
        ),
        entity_type=entity_type,
        entity_id=entity_id,
        expected_amount=expected,
        observed_amount=observed,
        leakage_amount=amount,
        explanation=explanation,
        evidence=evidence,
    )


def detect_revenue_leakage(
    *,
    invoices: list[dict[str, Any]] | None = None,
    payments: list[dict[str, Any]] | None = None,
    refunds: list[dict[str, Any]] | None = None,
    disputes: list[dict[str, Any]] | None = None,
    settlements: list[dict[str, Any]] | None = None,
    orders: list[dict[str, Any]] | None = None,
) -> tuple[RevenueLeakage, ...]:

    invoices = invoices or []
    payments = payments or []
    refunds = refunds or []
    disputes = disputes or []
    settlements = settlements or []
    orders = orders or []

    # Settlement index must exist BEFORE payment analysis.
    # This prevents a settlement-linked payment from being
    # incorrectly classified as an orphan payment.
    settled_by_payment: dict[str, float] = {}

    for settlement in settlements:
        payment_id = settlement.get("payment_id")

        if not payment_id:
            continue

        payment_key = str(payment_id)

        settled_by_payment[payment_key] = (
            settled_by_payment.get(
                payment_key,
                0.0,
            )
            + _money(
                settlement.get("amount")
            )
        )

    leakages: list[RevenueLeakage] = []

    payments_by_invoice: dict[str, float] = {}

    for payment in payments:
        invoice_id = payment.get(
            "invoice_id"
        )

        if invoice_id:
            payments_by_invoice[invoice_id] = (
                payments_by_invoice.get(
                    invoice_id,
                    0.0,
                )
                + _money(
                    payment.get("amount")
                )
            )

    payment_ids = {
        str(
            payment.get(
                "payment_id",
                payment.get("id", ""),
            )
        )
        for payment in payments
    }

    order_ids = {
        str(
            order.get(
                "order_id",
                order.get("id", ""),
            )
        )
        for order in orders
    }

    # --------------------------------------------------------
    # Invoice leakage
    # --------------------------------------------------------

    for invoice in invoices:
        invoice_id = str(
            invoice.get(
                "invoice_id",
                invoice.get("id", ""),
            )
        )

        if not invoice_id:
            continue

        expected = _money(
            invoice.get(
                "amount",
                invoice.get(
                    "total_amount",
                    invoice.get(
                        "expected_amount",
                        0,
                    ),
                ),
            )
        )

        outstanding = _money(
            invoice.get(
                "outstanding_amount",
                invoice.get(
                    "amount_due",
                    0,
                ),
            )
        )

        paid = payments_by_invoice.get(
            invoice_id,
            max(expected - outstanding, 0.0),
        )

        if outstanding > 0:
            leakage_type = (
                LeakageType.PARTIAL_PAYMENT
                if paid > 0
                else LeakageType.UNPAID_INVOICE
            )

            leakages.append(
                _leakage(
                    leakage_type=leakage_type,
                    entity_type="invoice",
                    entity_id=invoice_id,
                    expected=expected,
                    observed=paid,
                    explanation=(
                        "Invoice value exceeds "
                        "observed collection."
                    ),
                    evidence=(
                        f"expected={expected:.2f}",
                        f"paid={paid:.2f}",
                        f"outstanding={outstanding:.2f}",
                    ),
                )
            )

        if invoice_id not in payments_by_invoice:
            # Only create orphan invoice exposure when
            # there is no explicit outstanding amount.
            if expected > 0 and outstanding <= 0:
                leakages.append(
                    _leakage(
                        leakage_type=(
                            LeakageType.ORPHAN_INVOICE
                        ),
                        entity_type="invoice",
                        entity_id=invoice_id,
                        expected=expected,
                        observed=0.0,
                        explanation=(
                            "Invoice has no linked "
                            "payment evidence."
                        ),
                        evidence=(
                            f"expected={expected:.2f}",
                            "linked_payments=0",
                        ),
                    )
                )

    # --------------------------------------------------------
    # Payment leakage
    # --------------------------------------------------------

    invoice_ids = {
        str(
            invoice.get(
                "invoice_id",
                invoice.get("id", ""),
            )
        )
        for invoice in invoices
    }

    for payment in payments:
        payment_id = str(
            payment.get(
                "payment_id",
                payment.get("id", ""),
            )
        )

        if not payment_id:
            continue

        amount = _money(
            payment.get("amount")
        )

        invoice_id = payment.get(
            "invoice_id"
        )

        if invoice_id and str(invoice_id) not in invoice_ids:
            leakages.append(
                _leakage(
                    leakage_type=(
                        LeakageType.PAYMENT_MISMATCH
                    ),
                    entity_type="payment",
                    entity_id=payment_id,
                    expected=amount,
                    observed=0.0,
                    explanation=(
                        "Payment references an "
                        "invoice that is absent "
                        "from the observed dataset."
                    ),
                    evidence=(
                        f"payment={payment_id}",
                        f"invoice={invoice_id}",
                        f"amount={amount:.2f}",
                    ),
                )
            )

        if not invoice_id:
            # A payment without an invoice is only orphaned
            # when it also has no settlement evidence.
            #
            # If a settlement exists, the payment is connected
            # to the revenue lifecycle and any shortfall is
            # correctly represented by SETTLEMENT_GAP.
            if payment_id not in settled_by_payment:
                leakages.append(
                    _leakage(
                        leakage_type=(
                            LeakageType.ORPHAN_PAYMENT
                        ),
                        entity_type="payment",
                        entity_id=payment_id,
                        expected=amount,
                        observed=0.0,
                        explanation=(
                            "Payment has no linked "
                            "invoice or settlement evidence."
                        ),
                        evidence=(
                            f"amount={amount:.2f}",
                            "invoice_link=missing",
                            "settlement_link=missing",
                        ),
                    )
                )

    # --------------------------------------------------------
    # Refund exposure
    # --------------------------------------------------------

    for refund in refunds:
        refund_id = str(
            refund.get(
                "refund_id",
                refund.get("id", ""),
            )
        )

        if not refund_id:
            continue

        amount = _money(
            refund.get("amount")
        )

        if amount > 0:
            leakages.append(
                _leakage(
                    leakage_type=(
                        LeakageType.REFUND_EXPOSURE
                    ),
                    entity_type="refund",
                    entity_id=refund_id,
                    expected=amount,
                    observed=0.0,
                    explanation=(
                        "Refund represents revenue "
                        "reversal exposure."
                    ),
                    evidence=(
                        f"refund_amount={amount:.2f}",
                    ),
                )
            )

    # --------------------------------------------------------
    # Dispute exposure
    # --------------------------------------------------------

    for dispute in disputes:
        dispute_id = str(
            dispute.get(
                "dispute_id",
                dispute.get("id", ""),
            )
        )

        if not dispute_id:
            continue

        amount = _money(
            dispute.get(
                "amount",
                dispute.get(
                    "disputed_amount",
                    0,
                ),
            )
        )

        if amount > 0:
            leakages.append(
                _leakage(
                    leakage_type=(
                        LeakageType.DISPUTE_EXPOSURE
                    ),
                    entity_type="dispute",
                    entity_id=dispute_id,
                    expected=amount,
                    observed=0.0,
                    explanation=(
                        "Dispute represents revenue "
                        "at risk."
                    ),
                    evidence=(
                        f"disputed_amount={amount:.2f}",
                    ),
                )
            )

    # --------------------------------------------------------
    # Settlement gaps
    # --------------------------------------------------------

    payments_by_id = {
        str(
            payment.get(
                "payment_id",
                payment.get("id", ""),
            )
        ): _money(
            payment.get("amount")
        )
        for payment in payments
    }

    # --------------------------------------------------------
    # Deterministic ordering
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Settlement gap detection
    # --------------------------------------------------------
    #
    # A payment that has settlement evidence must not be
    # classified as orphaned. If the settled amount is lower
    # than the payment amount, emit exactly one SETTLEMENT_GAP
    # leakage signal for that payment.
    #
    # This is intentionally independent from invoice/order
    # intelligence so the settlement lifecycle can be analyzed
    # even when those datasets are absent.

    payment_by_id: dict[str, float] = {}

    for payment in payments:
        payment_id = str(
            payment.get(
                "payment_id",
                payment.get("id", ""),
            )
        )

        if not payment_id:
            continue

        payment_by_id[payment_id] = (
            payment_by_id.get(
                payment_id,
                0.0,
            )
            + _money(
                payment.get("amount")
            )
        )

    for payment_id, payment_amount in payment_by_id.items():
        settled_amount = settled_by_payment.get(
            payment_id,
            0.0,
        )

        if (
            payment_id in settled_by_payment
            and settled_amount < payment_amount
        ):
            gap = payment_amount - settled_amount

            if gap > 0:
                leakages.append(
                    _leakage(
                        leakage_type=(
                            LeakageType.SETTLEMENT_GAP
                        ),
                        entity_type="payment",
                        entity_id=payment_id,
                        expected=payment_amount,
                        observed=settled_amount,
                        explanation=(
                            "Payment amount exceeds "
                            "the amount represented "
                            "by settlement evidence."
                        ),
                        evidence=(
                            f"payment={payment_id}",
                            f"payment_amount={payment_amount:.2f}",
                            f"settled={settled_amount:.2f}",
                            f"gap={gap:.2f}",
                        ),
                    )
                )

    return tuple(
        sorted(
            leakages,
            key=lambda item: (
                -item.leakage_amount,
                item.leakage_id,
            ),
        )
    )


def summarize_revenue_leakage(
    leakages: tuple[
        RevenueLeakage,
        ...,
    ]
    | list[RevenueLeakage],
) -> RevenueLeakageReport:

    items = tuple(leakages)

    def amount(
        leakage_type: LeakageType,
    ) -> float:
        return sum(
            item.leakage_amount
            for item in items
            if item.leakage_type
            == leakage_type
        )

    total = sum(
        item.leakage_amount
        for item in items
    )

    critical = sum(
        item.severity
        == LeakageSeverity.CRITICAL
        for item in items
    )

    high = sum(
        item.severity
        == LeakageSeverity.HIGH
        for item in items
    )

    medium = sum(
        item.severity
        == LeakageSeverity.MEDIUM
        for item in items
    )

    low = sum(
        item.severity
        == LeakageSeverity.LOW
        for item in items
    )

    if not items:
        summary = (
            "No revenue leakage detected "
            "from the observed dataset."
        )
    else:
        summary = (
            f"{len(items)} revenue leakage "
            f"signal(s) detected with total "
            f"exposure of ₹{total:,.2f}. "
            f"{critical} critical and "
            f"{high} high-severity signal(s) "
            "require review."
        )

    return RevenueLeakageReport(
        total_leakage_amount=total,
        leakage_count=len(items),
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        low_count=low,
        unpaid_invoice_exposure=amount(
            LeakageType.UNPAID_INVOICE
        ),
        partial_payment_exposure=amount(
            LeakageType.PARTIAL_PAYMENT
        ),
        payment_mismatch_exposure=amount(
            LeakageType.PAYMENT_MISMATCH
        ),
        refund_exposure=amount(
            LeakageType.REFUND_EXPOSURE
        ),
        dispute_exposure=amount(
            LeakageType.DISPUTE_EXPOSURE
        ),
        settlement_gap_exposure=amount(
            LeakageType.SETTLEMENT_GAP
        ),
        orphan_exposure=(
            amount(
                LeakageType.ORPHAN_PAYMENT
            )
            + amount(
                LeakageType.ORPHAN_INVOICE
            )
            + amount(
                LeakageType.ORPHAN_ORDER
            )
        ),
        executive_summary=summary,
        leakages=items,
    )
