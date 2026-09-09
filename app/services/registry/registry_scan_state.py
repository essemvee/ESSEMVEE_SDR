from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.registry.registry_state import DEFAULT_DB_PATH


# ============================================================
# REGISTRY SCAN STATE
# ============================================================

DEFAULT_SCAN_STATE_DB_PATH = DEFAULT_DB_PATH


def utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


class RegistryScanStateStore:
    """
    Persistent state for dataset-level registry scanning.

    Company-level state is handled by RegistryStateStore.

    This class tracks where a large registry scan has reached so
    the scanner can resume safely after interruption.
    """

    def __init__(
        self,
        db_path: str | Path = DEFAULT_SCAN_STATE_DB_PATH,
    ) -> None:

        self.db_path = Path(db_path)

        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
        )

        self._connection.row_factory = sqlite3.Row

        self._create_tables()

    # ========================================================
    # DATABASE
    # ========================================================

    def _create_tables(self) -> None:

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS registry_scan_state (
                source TEXT PRIMARY KEY,

                status TEXT NOT NULL,

                current_offset INTEGER NOT NULL DEFAULT 0,

                batch_size INTEGER NOT NULL DEFAULT 1000,

                records_processed INTEGER NOT NULL DEFAULT 0,

                records_new INTEGER NOT NULL DEFAULT 0,

                records_changed INTEGER NOT NULL DEFAULT 0,

                records_unchanged INTEGER NOT NULL DEFAULT 0,

                records_invalid INTEGER NOT NULL DEFAULT 0,

                scan_started_at TEXT,

                scan_completed_at TEXT,

                last_batch_started_at TEXT,

                last_batch_completed_at TEXT,

                last_error TEXT
            )
            """
        )

        self._connection.commit()

    # ========================================================
    # CONNECTION
    # ========================================================

    def close(self) -> None:
        """Close the SQLite connection."""

        if self._connection is not None:
            self._connection.close()

    # ========================================================
    # GET STATE
    # ========================================================

    def get(
        self,
        source: str,
    ) -> dict[str, Any] | None:

        row = self._connection.execute(
            """
            SELECT *
            FROM registry_scan_state
            WHERE source = ?
            """,
            (source,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    # ========================================================
    # INITIALIZE SCAN
    # ========================================================

    def start_scan(
        self,
        source: str,
        batch_size: int = 1000,
    ) -> dict[str, Any]:

        if not source or not source.strip():
            raise ValueError(
                "source must not be empty."
            )

        if batch_size < 1:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        existing = self.get(
            source
        )

        now = utc_now()

        if existing is None:

            self._connection.execute(
                """
                INSERT INTO registry_scan_state (
                    source,
                    status,
                    current_offset,
                    batch_size,
                    records_processed,
                    records_new,
                    records_changed,
                    records_unchanged,
                    records_invalid,
                    scan_started_at,
                    scan_completed_at,
                    last_batch_started_at,
                    last_batch_completed_at,
                    last_error
                )
                VALUES (
                    ?,
                    'RUNNING',
                    0,
                    ?,
                    0,
                    0,
                    0,
                    0,
                    0,
                    ?,
                    NULL,
                    NULL,
                    NULL,
                    NULL
                )
                """,
                (
                    source,
                    batch_size,
                    now,
                ),
            )

        else:

            self._connection.execute(
                """
                UPDATE registry_scan_state
                SET
                    status = 'RUNNING',
                    batch_size = ?,
                    scan_started_at = ?,
                    scan_completed_at = NULL,
                    last_error = NULL
                WHERE source = ?
                """,
                (
                    batch_size,
                    now,
                    source,
                ),
            )

        self._connection.commit()

        return self.get(source)

    # ========================================================
    # BATCH START
    # ========================================================

    def start_batch(
        self,
        source: str,
    ) -> dict[str, Any]:

        existing = self.get(
            source
        )

        if existing is None:
            raise ValueError(
                f"No scan state exists for source: {source}"
            )

        if existing["status"] != "RUNNING":
            raise ValueError(
                f"Scan is not running for source: {source}"
            )

        now = utc_now()

        self._connection.execute(
            """
            UPDATE registry_scan_state
            SET last_batch_started_at = ?
            WHERE source = ?
            """,
            (
                now,
                source,
            ),
        )

        self._connection.commit()

        return self.get(source)

    # ========================================================
    # BATCH SUCCESS
    # ========================================================

    def complete_batch(
        self,
        source: str,
        records_processed: int,
        records_new: int = 0,
        records_changed: int = 0,
        records_unchanged: int = 0,
        records_invalid: int = 0,
        next_offset: int | None = None,
    ) -> dict[str, Any]:

        if records_processed < 0:
            raise ValueError(
                "records_processed cannot be negative."
            )

        if records_new < 0:
            raise ValueError(
                "records_new cannot be negative."
            )

        if records_changed < 0:
            raise ValueError(
                "records_changed cannot be negative."
            )

        if records_unchanged < 0:
            raise ValueError(
                "records_unchanged cannot be negative."
            )

        if records_invalid < 0:
            raise ValueError(
                "records_invalid cannot be negative."
            )

        existing = self.get(
            source
        )

        if existing is None:
            raise ValueError(
                f"No scan state exists for source: {source}"
            )

        if next_offset is None:
            next_offset = (
                existing["current_offset"]
                + records_processed
            )

        if next_offset < 0:
            raise ValueError(
                "next_offset cannot be negative."
            )

        now = utc_now()

        self._connection.execute(
            """
            UPDATE registry_scan_state
            SET
                current_offset = ?,
                records_processed = records_processed + ?,
                records_new = records_new + ?,
                records_changed = records_changed + ?,
                records_unchanged = records_unchanged + ?,
                records_invalid = records_invalid + ?,
                last_batch_completed_at = ?,
                last_error = NULL
            WHERE source = ?
            """,
            (
                next_offset,
                records_processed,
                records_new,
                records_changed,
                records_unchanged,
                records_invalid,
                now,
                source,
            ),
        )

        self._connection.commit()

        return self.get(source)

    # ========================================================
    # SCAN COMPLETE
    # ========================================================

    def complete_scan(
        self,
        source: str,
    ) -> dict[str, Any]:

        existing = self.get(
            source
        )

        if existing is None:
            raise ValueError(
                f"No scan state exists for source: {source}"
            )

        now = utc_now()

        self._connection.execute(
            """
            UPDATE registry_scan_state
            SET
                status = 'COMPLETED',
                scan_completed_at = ?,
                last_error = NULL
            WHERE source = ?
            """,
            (
                now,
                source,
            ),
        )

        self._connection.commit()

        return self.get(source)

    # ========================================================
    # SCAN FAILURE
    # ========================================================

    def fail_scan(
        self,
        source: str,
        error: str,
    ) -> dict[str, Any]:

        existing = self.get(
            source
        )

        if existing is None:
            raise ValueError(
                f"No scan state exists for source: {source}"
            )

        now = utc_now()

        self._connection.execute(
            """
            UPDATE registry_scan_state
            SET
                status = 'FAILED',
                last_error = ?,
                last_batch_completed_at = ?
            WHERE source = ?
            """,
            (
                str(error),
                now,
                source,
            ),
        )

        self._connection.commit()

        return self.get(source)

    # ========================================================
    # RESET SCAN
    # ========================================================

    def reset_scan(
        self,
        source: str,
        batch_size: int | None = None,
    ) -> dict[str, Any]:

        existing = self.get(
            source
        )

        if existing is None:
            raise ValueError(
                f"No scan state exists for source: {source}"
            )

        if batch_size is None:
            batch_size = existing["batch_size"]

        if batch_size < 1:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        self._connection.execute(
            """
            UPDATE registry_scan_state
            SET
                status = 'RESET',
                current_offset = 0,
                batch_size = ?,
                records_processed = 0,
                records_new = 0,
                records_changed = 0,
                records_unchanged = 0,
                records_invalid = 0,
                scan_started_at = NULL,
                scan_completed_at = NULL,
                last_batch_started_at = NULL,
                last_batch_completed_at = NULL,
                last_error = NULL
            WHERE source = ?
            """,
            (
                batch_size,
                source,
            ),
        )

        self._connection.commit()

        return self.get(source)

    # ========================================================
    # COUNT
    # ========================================================

    def count(self) -> int:

        row = self._connection.execute(
            """
            SELECT COUNT(*)
            AS count
            FROM registry_scan_state
            """
        ).fetchone()

        return int(
            row["count"]
        )


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "Registry scan state module loaded successfully."
    )