"""Persistent execution state for the autonomous ESSEMVEE SDR.

This module owns durable prospect, sequence, message, suppression and audit
state.  It intentionally uses only the Python standard library so the state
engine can run before any email/calendar provider is connected.

The database lives under ``data/`` by default and is therefore local runtime
state, not source-controlled application data.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SDR_DB_PATH = Path("data") / "sdr_state.sqlite3"


class SDRStatus(str, Enum):
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    CONTACT_FOUND = "CONTACT_FOUND"
    READY_TO_CONTACT = "READY_TO_CONTACT"
    EMAIL_SENT = "EMAIL_SENT"
    WAITING_FOR_REPLY = "WAITING_FOR_REPLY"
    FOLLOWUP_1_DUE = "FOLLOWUP_1_DUE"
    FOLLOWUP_1_SENT = "FOLLOWUP_1_SENT"
    FOLLOWUP_2_DUE = "FOLLOWUP_2_DUE"
    FOLLOWUP_2_SENT = "FOLLOWUP_2_SENT"
    FOLLOWUP_3_DUE = "FOLLOWUP_3_DUE"
    FOLLOWUP_3_SENT = "FOLLOWUP_3_SENT"
    POSITIVE_REPLY = "POSITIVE_REPLY"
    NEGATIVE_REPLY = "NEGATIVE_REPLY"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    BOUNCED = "BOUNCED"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    MEETING_REQUESTED = "MEETING_REQUESTED"
    MEETING_PROPOSED = "MEETING_PROPOSED"
    MEETING_BOOKED = "MEETING_BOOKED"
    SEQUENCE_COMPLETE = "SEQUENCE_COMPLETE"


STOP_STATUSES = frozenset(
    {
        SDRStatus.NEGATIVE_REPLY,
        SDRStatus.UNSUBSCRIBED,
        SDRStatus.BOUNCED,
        SDRStatus.HUMAN_HANDOFF,
        SDRStatus.MEETING_BOOKED,
        SDRStatus.SEQUENCE_COMPLETE,
    }
)


@dataclass(frozen=True)
class SDRProspect:
    prospect_key: str
    company_name: str
    contact_email: str | None
    contact_name: str | None
    contact_role: str | None
    status: SDRStatus
    sequence_name: str
    sequence_step: int
    next_action_at: str | None
    thread_id: str | None
    last_message_id: str | None
    stop_reason: str | None
    last_error: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SDREvent:
    id: int
    prospect_key: str
    event_type: str
    event_at: str
    metadata: dict[str, Any]
    idempotency_key: str | None


class SDRExecutionState:
    """SQLite-backed, restart-safe state store for SDR execution."""

    def __init__(self, db_path: str | Path = DEFAULT_SDR_DB_PATH) -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        self._create_schema()

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def normalise_key(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def make_prospect_key(
        source: str,
        source_record_id: str | int,
        contact_email: str,
    ) -> str:
        raw = "|".join(
            [
                SDRExecutionState.normalise_key(source),
                str(source_record_id).strip(),
                SDRExecutionState.normalise_key(contact_email),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sdr_prospects (
                prospect_key TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                contact_email TEXT,
                contact_name TEXT,
                contact_role TEXT,
                status TEXT NOT NULL,
                sequence_name TEXT NOT NULL,
                sequence_step INTEGER NOT NULL DEFAULT 0,
                next_action_at TEXT,
                thread_id TEXT,
                last_message_id TEXT,
                stop_reason TEXT,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_sdr_prospects_status
                ON sdr_prospects(status);
            CREATE INDEX IF NOT EXISTS idx_sdr_prospects_next_action
                ON sdr_prospects(next_action_at);
            CREATE INDEX IF NOT EXISTS idx_sdr_prospects_email
                ON sdr_prospects(contact_email);

            CREATE TABLE IF NOT EXISTS sdr_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_key TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                idempotency_key TEXT UNIQUE,
                FOREIGN KEY(prospect_key) REFERENCES sdr_prospects(prospect_key)
            );

            CREATE INDEX IF NOT EXISTS idx_sdr_events_prospect
                ON sdr_events(prospect_key, id);

            CREATE TABLE IF NOT EXISTS sdr_messages (
                message_id TEXT PRIMARY KEY,
                prospect_key TEXT NOT NULL,
                direction TEXT NOT NULL,
                provider TEXT,
                thread_id TEXT,
                sent_at TEXT,
                received_at TEXT,
                subject TEXT,
                status TEXT NOT NULL,
                FOREIGN KEY(prospect_key) REFERENCES sdr_prospects(prospect_key)
            );

            CREATE INDEX IF NOT EXISTS idx_sdr_messages_prospect
                ON sdr_messages(prospect_key, direction);

            CREATE TABLE IF NOT EXISTS sdr_suppressions (
                suppression_key TEXT PRIMARY KEY,
                suppression_type TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SDRExecutionState":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _row_to_prospect(self, row: sqlite3.Row | None) -> SDRProspect | None:
        if row is None:
            return None
        return SDRProspect(
            prospect_key=row["prospect_key"],
            company_name=row["company_name"],
            contact_email=row["contact_email"],
            contact_name=row["contact_name"],
            contact_role=row["contact_role"],
            status=SDRStatus(row["status"]),
            sequence_name=row["sequence_name"],
            sequence_step=row["sequence_step"],
            next_action_at=row["next_action_at"],
            thread_id=row["thread_id"],
            last_message_id=row["last_message_id"],
            stop_reason=row["stop_reason"],
            last_error=row["last_error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_prospect(self, prospect_key: str) -> SDRProspect | None:
        row = self._connection.execute(
            "SELECT * FROM sdr_prospects WHERE prospect_key = ?",
            (prospect_key,),
        ).fetchone()
        return self._row_to_prospect(row)

    def upsert_prospect(
        self,
        *,
        prospect_key: str,
        company_name: str,
        contact_email: str | None,
        contact_name: str | None = None,
        contact_role: str | None = None,
        status: SDRStatus = SDRStatus.NEW,
        sequence_name: str = "default",
        sequence_step: int = 0,
        next_action_at: str | None = None,
    ) -> SDRProspect:
        now = self.utc_now()
        existing = self.get_prospect(prospect_key)
        if existing is None:
            self._connection.execute(
                """
                INSERT INTO sdr_prospects (
                    prospect_key, company_name, contact_email, contact_name,
                    contact_role, status, sequence_name, sequence_step,
                    next_action_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prospect_key,
                    company_name,
                    contact_email,
                    contact_name,
                    contact_role,
                    status.value,
                    sequence_name,
                    sequence_step,
                    next_action_at,
                    now,
                    now,
                ),
            )
            self._connection.commit()
        else:
            self._connection.execute(
                """
                UPDATE sdr_prospects
                SET company_name = ?, contact_email = ?, contact_name = ?,
                    contact_role = ?, sequence_name = ?, updated_at = ?
                WHERE prospect_key = ?
                """,
                (
                    company_name,
                    contact_email,
                    contact_name,
                    contact_role,
                    sequence_name,
                    now,
                    prospect_key,
                ),
            )
            self._connection.commit()
        return self.get_prospect(prospect_key)  # type: ignore[return-value]

    def transition(
        self,
        prospect_key: str,
        new_status: SDRStatus,
        *,
        next_action_at: str | None = None,
        sequence_step: int | None = None,
        stop_reason: str | None = None,
        last_error: str | None = None,
        event_type: str | None = None,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> SDRProspect:
        current = self.get_prospect(prospect_key)
        if current is None:
            raise KeyError(f"Unknown SDR prospect: {prospect_key}")

        now = self.utc_now()
        if new_status in STOP_STATUSES:
            next_action_at = None
            stop_reason = stop_reason or new_status.value

        self._connection.execute(
            """
            UPDATE sdr_prospects
            SET status = ?, sequence_step = COALESCE(?, sequence_step),
                next_action_at = ?, stop_reason = ?, last_error = ?,
                updated_at = ?
            WHERE prospect_key = ?
            """,
            (
                new_status.value,
                sequence_step,
                next_action_at,
                stop_reason,
                last_error,
                now,
                prospect_key,
            ),
        )
        self._connection.commit()

        self.record_event(
            prospect_key,
            event_type or "STATUS_CHANGED",
            metadata={
                "from_status": current.status.value,
                "to_status": new_status.value,
                **(metadata or {}),
            },
            idempotency_key=idempotency_key,
        )
        return self.get_prospect(prospect_key)  # type: ignore[return-value]

    def record_event(
        self,
        prospect_key: str,
        event_type: str,
        *,
        metadata: dict[str, Any] | None = None,
        event_at: str | None = None,
        idempotency_key: str | None = None,
    ) -> bool:
        if idempotency_key is not None:
            existing = self._connection.execute(
                "SELECT 1 FROM sdr_events WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                return False

        self._connection.execute(
            """
            INSERT INTO sdr_events (
                prospect_key, event_type, event_at, metadata_json, idempotency_key
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                prospect_key,
                event_type,
                event_at or self.utc_now(),
                json.dumps(metadata or {}, sort_keys=True),
                idempotency_key,
            ),
        )
        self._connection.commit()
        return True

    def list_events(self, prospect_key: str) -> list[SDREvent]:
        rows = self._connection.execute(
            "SELECT * FROM sdr_events WHERE prospect_key = ? ORDER BY id",
            (prospect_key,),
        ).fetchall()
        return [
            SDREvent(
                id=row["id"],
                prospect_key=row["prospect_key"],
                event_type=row["event_type"],
                event_at=row["event_at"],
                metadata=json.loads(row["metadata_json"]),
                idempotency_key=row["idempotency_key"],
            )
            for row in rows
        ]

    def record_message(
        self,
        *,
        message_id: str,
        prospect_key: str,
        direction: str,
        provider: str | None = None,
        thread_id: str | None = None,
        sent_at: str | None = None,
        received_at: str | None = None,
        subject: str | None = None,
        status: str = "RECORDED",
    ) -> bool:
        cursor = self._connection.execute(
            """
            INSERT OR IGNORE INTO sdr_messages (
                message_id, prospect_key, direction, provider, thread_id,
                sent_at, received_at, subject, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                prospect_key,
                direction,
                provider,
                thread_id,
                sent_at,
                received_at,
                subject,
                status,
            ),
        )
        inserted = cursor.rowcount == 1
        if inserted:
            now = self.utc_now()
            self._connection.execute(
                """
                UPDATE sdr_prospects
                SET thread_id = COALESCE(?, thread_id),
                    last_message_id = ?, updated_at = ?
                WHERE prospect_key = ?
                """,
                (thread_id, message_id, now, prospect_key),
            )
            self._connection.commit()
        return inserted

    def add_suppression(
        self,
        value: str,
        suppression_type: str,
        *,
        reason: str | None = None,
    ) -> bool:
        key = self.normalise_key(value)
        cursor = self._connection.execute(
            """
            INSERT OR IGNORE INTO sdr_suppressions (
                suppression_key, suppression_type, reason, created_at
            ) VALUES (?, ?, ?, ?)
            """,
            (key, suppression_type, reason, self.utc_now()),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def is_suppressed(self, value: str) -> bool:
        key = self.normalise_key(value)
        row = self._connection.execute(
            "SELECT 1 FROM sdr_suppressions WHERE suppression_key = ?",
            (key,),
        ).fetchone()
        return row is not None

    def due_prospects(self, *, now: str | None = None) -> list[SDRProspect]:
        current_time = now or self.utc_now()
        placeholders = ",".join("?" for _ in SDRStatus)
        stop_values = [status.value for status in STOP_STATUSES]
        rows = self._connection.execute(
            f"""
            SELECT * FROM sdr_prospects
            WHERE next_action_at IS NOT NULL
              AND next_action_at <= ?
              AND status NOT IN ({','.join('?' for _ in stop_values)})
            ORDER BY next_action_at, prospect_key
            """,
            (current_time, *stop_values),
        ).fetchall()
        return [self._row_to_prospect(row) for row in rows if row is not None]

    def count(self) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM sdr_prospects"
        ).fetchone()
        return int(row["count"])

    def clear(self) -> None:
        self._connection.executescript(
            """
            DELETE FROM sdr_messages;
            DELETE FROM sdr_events;
            DELETE FROM sdr_suppressions;
            DELETE FROM sdr_prospects;
            """
        )
        self._connection.commit()


__all__ = [
    "DEFAULT_SDR_DB_PATH",
    "SDREvent",
    "SDRExecutionState",
    "SDRProspect",
    "SDRStatus",
    "STOP_STATUSES",
]
