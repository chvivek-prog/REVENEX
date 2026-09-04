from __future__ import annotations

import sqlite3
from typing import Optional

from .contracts import (
    EventStatus,
    WebhookEvent,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS webhook_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    received_at REAL NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    signature_verified INTEGER NOT NULL DEFAULT 0,
    read_only INTEGER NOT NULL DEFAULT 1,
    financial_mutation INTEGER NOT NULL DEFAULT 0,
    provider_mutation INTEGER NOT NULL DEFAULT 0
);
"""


class EventStore:
    """
    Durable webhook/event store.

    Event persistence is not financial mutation.
    """

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
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def exists(self, event_id: str) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM webhook_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

        return row is not None

    def save(self, event: WebhookEvent) -> bool:
        """
        Save an event exactly once.

        Returns:
            True  = newly inserted
            False = duplicate
        """

        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO webhook_events (
                event_id,
                event_type,
                entity_type,
                entity_id,
                payload_hash,
                received_at,
                status,
                attempt_count,
                signature_verified,
                read_only,
                financial_mutation,
                provider_mutation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.event_type,
                event.entity_type,
                event.entity_id,
                event.payload_hash,
                event.received_at,
                event.status.value,
                event.attempt_count,
                int(event.signature_verified),
                1,
                0,
                0,
            ),
        )

        self.connection.commit()

        return cursor.rowcount == 1

    def update(
        self,
        event: WebhookEvent,
    ) -> WebhookEvent:
        self.connection.execute(
            """
            UPDATE webhook_events
            SET status = ?,
                attempt_count = ?,
                signature_verified = ?
            WHERE event_id = ?
            """,
            (
                event.status.value,
                event.attempt_count,
                int(event.signature_verified),
                event.event_id,
            ),
        )

        self.connection.commit()

        result = self.get(event.event_id)

        if result is None:
            raise KeyError(
                f"Unknown event_id: {event.event_id}"
            )

        return result

    def get(
        self,
        event_id: str,
    ) -> Optional[WebhookEvent]:
        row = self.connection.execute(
            """
            SELECT *
            FROM webhook_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

        if row is None:
            return None

        return WebhookEvent(
            event_id=row["event_id"],
            event_type=row["event_type"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            payload_hash=row["payload_hash"],
            received_at=float(row["received_at"]),
            status=EventStatus(row["status"]),
            attempt_count=int(row["attempt_count"]),
            signature_verified=bool(
                row["signature_verified"]
            ),
            read_only=bool(row["read_only"]),
            financial_mutation=bool(
                row["financial_mutation"]
            ),
            provider_mutation=bool(
                row["provider_mutation"]
            ),
        )
