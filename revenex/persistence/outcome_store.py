"""
REVENEX Stage 42 — Persistent Outcome & Learning Store.

SQLite-first durable storage for:
    Decision -> Outcome -> Evaluation -> Learning

The store is deliberately isolated from execution.
It does not perform provider or financial mutations.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS outcome_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    expected_collection REAL NOT NULL,
    actual_collection REAL,
    expected_remaining_exposure REAL NOT NULL,
    actual_remaining_exposure REAL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(decision_id)
);

CREATE TABLE IF NOT EXISTS outcome_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outcome_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    collection_variance REAL,
    collection_accuracy REAL,
    exposure_variance REAL,
    learning_signal TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(outcome_id)
        REFERENCES outcome_events(id)
);

CREATE TABLE IF NOT EXISTS learning_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    signal TEXT NOT NULL,
    strength REAL NOT NULL,
    evidence TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_outcome_decision
    ON outcome_events(decision_id);

CREATE INDEX IF NOT EXISTS idx_outcome_customer
    ON outcome_events(customer_id);

CREATE INDEX IF NOT EXISTS idx_learning_decision
    ON learning_signals(decision_id);
"""


@dataclass(frozen=True)
class StoredOutcome:
    id: int
    decision_id: str
    customer_id: str
    expected_collection: float
    actual_collection: Optional[float]
    expected_remaining_exposure: float
    actual_remaining_exposure: Optional[float]
    status: str


class OutcomeStore:
    """Durable SQLite store for the closed-loop intelligence layer."""

    def __init__(self, database: str | Path = ":memory:") -> None:
        self.database = str(database)

        self.connection = sqlite3.connect(
            self.database,
        )

        self.connection.row_factory = sqlite3.Row

        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def create_outcome(
        self,
        *,
        decision_id: str,
        customer_id: str,
        expected_collection: float,
        expected_remaining_exposure: float,
    ) -> StoredOutcome:
        """
        Create a pending outcome.

        Existing decision_id returns the existing record instead of
        creating a duplicate.
        """

        existing = self.connection.execute(
            """
            SELECT *
            FROM outcome_events
            WHERE decision_id = ?
            """,
            (decision_id,),
        ).fetchone()

        if existing is not None:
            return self._row_to_outcome(existing)

        cursor = self.connection.execute(
            """
            INSERT INTO outcome_events (
                decision_id,
                customer_id,
                expected_collection,
                expected_remaining_exposure,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                customer_id,
                float(expected_collection),
                float(expected_remaining_exposure),
                "PENDING",
            ),
        )

        self.connection.commit()

        row = self.connection.execute(
            """
            SELECT *
            FROM outcome_events
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "Outcome was inserted but could not be read back."
            )

        return self._row_to_outcome(row)

    def record_outcome(
        self,
        *,
        decision_id: str,
        actual_collection: float,
        actual_remaining_exposure: float,
        status: str = "OBSERVED",
    ) -> StoredOutcome:
        """
        Persist observed outcome values.

        Negative monetary values are normalized to zero.
        """

        row = self.connection.execute(
            """
            SELECT *
            FROM outcome_events
            WHERE decision_id = ?
            """,
            (decision_id,),
        ).fetchone()

        if row is None:
            raise KeyError(
                f"Unknown decision_id: {decision_id}"
            )

        self.connection.execute(
            """
            UPDATE outcome_events
            SET actual_collection = ?,
                actual_remaining_exposure = ?,
                status = ?
            WHERE decision_id = ?
            """,
            (
                max(0.0, float(actual_collection)),
                max(0.0, float(actual_remaining_exposure)),
                status,
                decision_id,
            ),
        )

        self.connection.commit()

        updated = self.connection.execute(
            """
            SELECT *
            FROM outcome_events
            WHERE decision_id = ?
            """,
            (decision_id,),
        ).fetchone()

        if updated is None:
            raise RuntimeError(
                "Outcome update could not be read back."
            )

        return self._row_to_outcome(updated)

    def record_evaluation(
        self,
        *,
        decision_id: str,
        status: str,
        collection_variance: float | None,
        collection_accuracy: float | None,
        exposure_variance: float | None,
        learning_signal: str,
    ) -> int:
        """Persist an evaluated outcome and return its evaluation id."""

        outcome = self.connection.execute(
            """
            SELECT id
            FROM outcome_events
            WHERE decision_id = ?
            """,
            (decision_id,),
        ).fetchone()

        if outcome is None:
            raise KeyError(
                f"Unknown decision_id: {decision_id}"
            )

        cursor = self.connection.execute(
            """
            INSERT INTO outcome_evaluations (
                outcome_id,
                status,
                collection_variance,
                collection_accuracy,
                exposure_variance,
                learning_signal
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                outcome["id"],
                status,
                collection_variance,
                collection_accuracy,
                exposure_variance,
                learning_signal,
            ),
        )

        self.connection.commit()

        return int(cursor.lastrowid)

    def record_learning_signal(
        self,
        *,
        decision_id: str,
        signal: str,
        strength: float,
        evidence: str,
    ) -> int:
        """Persist a learning signal."""

        cursor = self.connection.execute(
            """
            INSERT INTO learning_signals (
                decision_id,
                signal,
                strength,
                evidence
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                decision_id,
                signal,
                max(0.0, min(1.0, float(strength))),
                evidence,
            ),
        )

        self.connection.commit()

        return int(cursor.lastrowid)

    def get_outcome(
        self,
        decision_id: str,
    ) -> Optional[StoredOutcome]:
        row = self.connection.execute(
            """
            SELECT *
            FROM outcome_events
            WHERE decision_id = ?
            """,
            (decision_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_outcome(row)

    def list_learning_signals(
        self,
        decision_id: str | None = None,
    ) -> list[dict]:
        if decision_id is None:
            rows = self.connection.execute(
                """
                SELECT *
                FROM learning_signals
                ORDER BY id ASC
                """
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT *
                FROM learning_signals
                WHERE decision_id = ?
                ORDER BY id ASC
                """,
                (decision_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def _row_to_outcome(
        self,
        row: sqlite3.Row,
    ) -> StoredOutcome:
        return StoredOutcome(
            id=int(row["id"]),
            decision_id=row["decision_id"],
            customer_id=row["customer_id"],
            expected_collection=float(
                row["expected_collection"]
            ),
            actual_collection=(
                None
                if row["actual_collection"] is None
                else float(row["actual_collection"])
            ),
            expected_remaining_exposure=float(
                row["expected_remaining_exposure"]
            ),
            actual_remaining_exposure=(
                None
                if row["actual_remaining_exposure"] is None
                else float(row["actual_remaining_exposure"])
            ),
            status=row["status"],
        )
