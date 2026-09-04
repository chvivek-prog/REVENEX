
from __future__ import annotations

from typing import Any


def summarize_ledger_exposure(
    report: Any,
) -> dict[str, Any]:

    return {
        "total_reconciliation_records": (
            report.total_records
        ),
        "matched_records": (
            report.matched_records
        ),
        "partial_records": (
            report.partial_records
        ),
        "mismatched_records": (
            report.mismatched_records
        ),
        "missing_records": (
            report.missing_records
        ),
        "critical_records": (
            report.critical_records
        ),
        "high_records": (
            report.high_records
        ),
        "revenue_impact": round(
            report.total_revenue_impact,
            2,
        ),
        "requires_human_review": any(
            record.requires_human_review
            for record in report.records
        ),
        "automatic_correction": False,
        "financial_mutation": False,
    }
