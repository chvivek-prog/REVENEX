
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from revenex.reconciliation.contracts import (
    ReconciliationReport,
)


def build_exception_queue(
    report: ReconciliationReport,
) -> list[dict[str, Any]]:

    queue = []

    for record in report.records:

        if not record.requires_human_review:
            continue

        item = asdict(record)

        item["severity"] = (
            record.severity.value
        )

        item["status"] = (
            record.status.value
        )

        item["mismatch_type"] = (
            record.mismatch_type.value
        )

        item["evidence"] = list(
            record.evidence
        )

        queue.append(item)

    severity_rank = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
        "NONE": 0,
    }

    queue.sort(
        key=lambda item: (
            severity_rank.get(
                item["severity"],
                0,
            ),
            abs(
                float(
                    item["revenue_impact"]
                )
            ),
        ),
        reverse=True,
    )

    return queue
