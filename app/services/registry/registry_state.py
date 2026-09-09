from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("data") / "registry_state.sqlite3"


def utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _normalise_value(value: Any) -> Any:
    """Convert values into deterministic JSON-safe representations."""
    if isinstance(value, dict):
        return {
            str(key): _normalise_value(val)
            for key, val in sorted(
                value.items(),
                key=lambda item: str(item[0]),
            )
        }

    if isinstance(value, (list, tuple)):
        return [_normalise_value(item) for item in value]

    if isinstance(value, set):
        return sorted(_normalise_value(item) for item in value)

    if isinstance(value, datetime):
        return value.isoformat()

    return value


def record_fingerprint(record: dict[str, Any]) -> str:
    """
    Create a deterministic SHA-256 fingerprint for a registry record.

    Identity fields are excluded because they identify the record
    rather than describe its current state.
    """
    identity_fields = {
        "source_record_id",
        "company_num",
        "company_number",
        "company_id",
    }

    payload = {
        key: value
        for key, value in record.items()
        if key not in identity_fields
    }

    normalised = _normalise_value(payload)

    encoded = json.dumps(
        normalised,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


class RegistryStateStore:
    """
    Persistent state store for incremental registry processing.

    The store tracks a stable source record identity and the latest
    observed snapshot metadata so registry data can be classified as:

        NEW
        UNCHANGED
        CHANGED
    """

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB_PATH,
    ) -> None:
        self.db_path = Path(db_path)

        if self.db_path.parent:
            self.db_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.db_path)
        )
        connection.row_factory = sqlite3.Row
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS registry_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    source TEXT NOT NULL,
                    source_record_id TEXT NOT NULL,

                    company_name TEXT,
                    registration_date TEXT,
                    status TEXT,
                    nace_code TEXT,

                    data_hash TEXT NOT NULL,

                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    last_checked_at TEXT NOT NULL,

                    check_count INTEGER NOT NULL DEFAULT 1,

                    UNIQUE(source, source_record_id)
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_registry_records_source
                ON registry_records(source)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_registry_records_status
                ON registry_records(status)
                """
            )

            connection.commit()

    @staticmethod
    def _identity(
        record: dict[str, Any],
        source: str,
    ) -> tuple[str, str]:
        """
        Resolve the stable identity of a registry record.

        Preferred field:
            source_record_id

        Common fallback fields:
            company_num
            company_number
            company_id
        """
        source_record_id = record.get(
            "source_record_id"
        )

        if source_record_id is None:
            for field in (
                "company_num",
                "company_number",
                "company_id",
            ):
                value = record.get(field)

                if value is not None:
                    source_record_id = value
                    break

        if source_record_id is None:
            raise ValueError(
                "Registry record does not contain "
                "a stable source record ID"
            )

        source_record_id = str(
            source_record_id
        ).strip()

        if not source_record_id:
            raise ValueError(
                "Registry record contains "
                "an empty source record ID"
            )

        source = str(source).strip()

        if not source:
            raise ValueError(
                "Registry source cannot be empty"
            )

        return source, source_record_id

    def get(
        self,
        source: str,
        source_record_id: str,
    ) -> dict[str, Any] | None:
        """Return the stored state for one registry record."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    source,
                    source_record_id,
                    company_name,
                    registration_date,
                    status,
                    nace_code,
                    data_hash,
                    first_seen_at,
                    last_seen_at,
                    last_checked_at,
                    check_count
                FROM registry_records
                WHERE source = ?
                  AND source_record_id = ?
                """,
                (
                    source,
                    str(source_record_id),
                ),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def classify_record(
        self,
        record: dict[str, Any],
        source: str,
    ) -> str:
        """
        Classify a registry record without modifying persistent state.

        Returns:

            NEW
            UNCHANGED
            CHANGED
        """
        source_name, source_record_id = self._identity(
            record,
            source,
        )

        existing = self.get(
            source_name,
            source_record_id,
        )

        if existing is None:
            return "NEW"

        current_hash = record_fingerprint(
            record
        )

        if existing["data_hash"] == current_hash:
            return "UNCHANGED"

        return "CHANGED"

    def record_seen(
        self,
        record: dict[str, Any],
        source: str,
    ) -> str:
        """
        Persist the current registry snapshot.

        Returns:

            NEW
            UNCHANGED
            CHANGED
        """
        source_name, source_record_id = self._identity(
            record,
            source,
        )

        current_hash = record_fingerprint(
            record
        )

        now = utc_now()

        existing = self.get(
            source_name,
            source_record_id,
        )

        if existing is None:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO registry_records (
                        source,
                        source_record_id,
                        company_name,
                        registration_date,
                        status,
                        nace_code,
                        data_hash,
                        first_seen_at,
                        last_seen_at,
                        last_checked_at,
                        check_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source_name,
                        source_record_id,
                        record.get("company_name"),
                        (
                            record.get(
                                "company_reg_date"
                            )
                            or record.get(
                                "registration_date"
                            )
                        ),
                        (
                            record.get(
                                "company_status"
                            )
                            or record.get(
                                "status"
                            )
                        ),
                        (
                            record.get(
                                "nace_v2_code"
                            )
                            or record.get(
                                "nace_code"
                            )
                        ),
                        current_hash,
                        now,
                        now,
                        now,
                        1,
                    ),
                )

                connection.commit()

            return "NEW"

        if existing["data_hash"] == current_hash:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE registry_records
                    SET
                        last_seen_at = ?,
                        last_checked_at = ?,
                        check_count = check_count + 1
                    WHERE source = ?
                      AND source_record_id = ?
                    """,
                    (
                        now,
                        now,
                        source_name,
                        source_record_id,
                    ),
                )

                connection.commit()

            return "UNCHANGED"

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE registry_records
                SET
                    company_name = ?,
                    registration_date = ?,
                    status = ?,
                    nace_code = ?,
                    data_hash = ?,
                    last_seen_at = ?,
                    last_checked_at = ?,
                    check_count = check_count + 1
                WHERE source = ?
                  AND source_record_id = ?
                """,
                (
                    record.get("company_name"),
                    (
                        record.get(
                            "company_reg_date"
                        )
                        or record.get(
                            "registration_date"
                        )
                    ),
                    (
                        record.get(
                            "company_status"
                        )
                        or record.get(
                            "status"
                        )
                    ),
                    (
                        record.get(
                            "nace_v2_code"
                        )
                        or record.get(
                            "nace_code"
                        )
                    ),
                    current_hash,
                    now,
                    now,
                    source_name,
                    source_record_id,
                ),
            )

            connection.commit()

        return "CHANGED"

    def count(
        self,
        source: str | None = None,
    ) -> int:
        """Return the number of persisted registry records."""
        with self._connect() as connection:
            if source is None:
                row = connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM registry_records
                    """
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM registry_records
                    WHERE source = ?
                    """,
                    (source,),
                ).fetchone()

        return int(row["count"])

    def clear(self) -> None:
        """Delete all persisted registry state."""
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM registry_records"
            )
            connection.commit()


__all__ = [
    "DEFAULT_DB_PATH",
    "RegistryStateStore",
    "record_fingerprint",
    "utc_now",
]