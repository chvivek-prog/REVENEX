
from __future__ import annotations

import json
import sqlite3

from revenex.reconciliation.contracts import (
    ReconciliationRecord,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS reconciliation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_id TEXT NOT NULL UNIQUE,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    status TEXT NOT NULL,
    mismatch_type TEXT NOT NULL,
    expected_amount REAL,
    observed_amount REAL,
    internal_amount REAL,
    amount_variance REAL,
    revenue_impact REAL NOT NULL,
    severity TEXT NOT NULL,
    explanation TEXT NOT NULL,
    requires_human_review INTEGER NOT NULL,
    evidence TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
idx_reconciliation_resource
ON reconciliation_records(resource_type, resource_id);

CREATE INDEX IF NOT EXISTS
idx_reconciliation_severity
ON reconciliation_records(severity);
"""


class ReconciliationStore:

    def __init__(
        self,
        connection: sqlite3.Connection | None = None,
    ) -> None:

        self.connection = (
            connection
            if connection is not None
            else sqlite3.connect(":memory:")
        )

        self.connection.row_factory = sqlite3.Row

        self.connection.executescript(
            SCHEMA
        )

        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def save(
        self,
        record: ReconciliationRecord,
    ) -> bool:

        existing = self.connection.execute(
            """
            SELECT 1
            FROM reconciliation_records
            WHERE reconciliation_id = ?
            """,
            (record.reconciliation_id,),
        ).fetchone()

        if existing is not None:
            return False

        self.connection.execute(
            """
            INSERT INTO reconciliation_records (
                reconciliation_id,
                resource_type,
                resource_id,
                status,
                mismatch_type,
                expected_amount,
                observed_amount,
                internal_amount,
                amount_variance,
                revenue_impact,
                severity,
                explanation,
                requires_human_review,
                evidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.reconciliation_id,
                record.resource_type,
                record.resource_id,
                record.status.value,
                record.mismatch_type.value,
                record.expected_amount,
                record.observed_amount,
                record.internal_amount,
                record.amount_variance,
                record.revenue_impact,
                record.severity.value,
                record.explanation,
                1 if record.requires_human_review else 0,
                json.dumps(
                    list(record.evidence)
                ),
            ),
        )

        self.connection.commit()

        return True

    def get(
        self,
        reconciliation_id: str,
    ) -> dict | None:

        row = self.connection.execute(
            """
            SELECT *
            FROM reconciliation_records
            WHERE reconciliation_id = ?
            """,
            (reconciliation_id,),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)

        result["evidence"] = json.loads(
            result["evidence"]
        )

        result["requires_human_review"] = bool(
            result["requires_human_review"]
        )

        return result

    def list(
        self,
    ) -> list[dict]:

        rows = self.connection.execute(
            """
            SELECT *
            FROM reconciliation_records
            ORDER BY id ASC
            """
        ).fetchall()

        result = []

        for row in rows:
            item = dict(row)

            item["evidence"] = json.loads(
                item["evidence"]
            )

            item["requires_human_review"] = bool(
                item["requires_human_review"]
            )

            result.append(item)

        return result
