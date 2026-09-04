from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "recoverai.sqlite3"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS recovery_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    status TEXT NOT NULL,
    failure_type TEXT,
    amount REAL NOT NULL DEFAULT 0,
    probability REAL,
    strategy TEXT,
    payload TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS recovery_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id TEXT NOT NULL,
    strategy TEXT NOT NULL,
    outcome TEXT NOT NULL,
    amount_recovered REAL NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
"""


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def record_event(
    *,
    payment_id: str,
    event_type: str,
    status: str,
    payload: dict[str, Any],
    failure_type: str | None = None,
    amount: float = 0,
    probability: float | None = None,
    strategy: str | None = None,
) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO recovery_events
        (
            payment_id,
            event_type,
            status,
            failure_type,
            amount,
            probability,
            strategy,
            payload,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payment_id,
            event_type,
            status,
            failure_type,
            float(amount or 0),
            probability,
            strategy,
            json.dumps(payload, sort_keys=True, default=str),
            time.time(),
        ),
    )
    conn.commit()
    conn.close()


def record_outcome(
    *,
    payment_id: str,
    strategy: str,
    outcome: str,
    amount_recovered: float = 0,
) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO recovery_outcomes
        (
            payment_id,
            strategy,
            outcome,
            amount_recovered,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            payment_id,
            strategy,
            outcome,
            float(amount_recovered or 0),
            time.time(),
        ),
    )
    conn.commit()
    conn.close()


def strategy_success_rate(
    failure_type: str,
) -> float | None:
    conn = _connect()

    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(
                CASE
                    WHEN outcome='RECOVERED'
                    THEN 1 ELSE 0
                END
            ) AS wins
        FROM recovery_outcomes ro
        JOIN recovery_events re
          ON re.payment_id = ro.payment_id
        WHERE re.failure_type=?
        """,
        (failure_type,),
    ).fetchone()

    conn.close()

    if not row or not row["total"]:
        return None

    return round(
        (row["wins"] or 0) / row["total"],
        4,
    )


def summary() -> dict[str, Any]:
    conn = _connect()

    failed = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM recovery_events
        WHERE event_type='PAYMENT_FAILED'
        """
    ).fetchone()["n"]

    pending = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM recovery_events
        WHERE event_type='PAYMENT_PENDING'
        """
    ).fetchone()["n"]

    recovered = conn.execute(
        """
        SELECT COALESCE(
            SUM(amount_recovered), 0
        ) AS n
        FROM recovery_outcomes
        WHERE outcome='RECOVERED'
        """
    ).fetchone()["n"]

    conn.close()

    return {
        "failed_payments": int(failed),
        "pending_payments": int(pending),
        "revenue_recovered": round(
            float(recovered),
            2,
        ),
    }
