
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from typing import Any

from revenex.events.contracts import (
    NormalizedEvent,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS provider_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    action TEXT NOT NULL,
    payload TEXT NOT NULL,
    sandbox INTEGER NOT NULL,
    processed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
idx_provider_events_resource
ON provider_events(resource_type, resource_id);

CREATE INDEX IF NOT EXISTS
idx_provider_events_type
ON provider_events(event_type);
"""


class EventStore:

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

    def exists(
        self,
        event_id: str,
    ) -> bool:

        row = self.connection.execute(
            """
            SELECT 1
            FROM provider_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

        return row is not None

    def append(
        self,
        event: NormalizedEvent,
    ) -> bool:

        if self.exists(event.event_id):
            return False

        self.connection.execute(
            """
            INSERT INTO provider_events (
                event_id,
                provider,
                event_type,
                occurred_at,
                resource_type,
                resource_id,
                action,
                payload,
                sandbox
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.provider,
                event.event_type,
                event.occurred_at,
                event.resource_type,
                event.resource_id,
                event.action,
                json.dumps(
                    event.payload,
                    sort_keys=True,
                    default=str,
                ),
                1 if event.sandbox else 0,
            ),
        )

        self.connection.commit()

        return True

    def mark_processed(
        self,
        event_id: str,
    ) -> None:

        self.connection.execute(
            """
            UPDATE provider_events
            SET processed = 1
            WHERE event_id = ?
            """,
            (event_id,),
        )

        self.connection.commit()

    def get(
        self,
        event_id: str,
    ) -> dict[str, Any] | None:

        row = self.connection.execute(
            """
            SELECT *
            FROM provider_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)

        result["payload"] = json.loads(
            result["payload"]
        )

        result["sandbox"] = bool(
            result["sandbox"]
        )

        result["processed"] = bool(
            result["processed"]
        )

        return result

    def list_events(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:

        rows = self.connection.execute(
            """
            SELECT *
            FROM provider_events
            ORDER BY id ASC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()

        result = []

        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(
                item["payload"]
            )
            item["sandbox"] = bool(
                item["sandbox"]
            )
            item["processed"] = bool(
                item["processed"]
            )
            result.append(item)

        return result
