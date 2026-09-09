from __future__ import annotations

"""
======================================================================
ESSEMVEE AI SDR
CRO SCANNER TEST SUITE
======================================================================

READ-ONLY TEST

Tests:

    1. First scan
    2. Resume from saved offset
    3. Re-scan after dataset exhaustion
    4. Scan state persistence

No live CRO data is modified.
No emails are sent.
No LinkedIn messages are sent.
No SDR records are modified.

Temporary SQLite databases are used.
======================================================================
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any

from app.services.registry.cro_scanner import CROScanner
from app.services.registry.ireland_cro import CRO_SOURCE
from app.services.registry.registry_scan_state import (
    RegistryScanStateStore,
)
from app.services.registry.registry_state import (
    RegistryStateStore,
)


# ======================================================================
# FAKE CRO
# ======================================================================


class FakeCRO:
    """
    Deterministic CRO adapter used only for scanner testing.
    """

    def __init__(
        self,
        records: list[dict[str, Any]],
        state_db_path: str | Path,
    ) -> None:
        self.records = list(records)

        self.state = RegistryStateStore(
            state_db_path
        )

    def fetch_records(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        if offset < 0:
            raise ValueError(
                "offset cannot be negative."
            )

        return self.records[
            offset : offset + limit
        ]

    def _state_record(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "company_num": record.get(
                "company_num"
            ),
            "company_name": record.get(
                "company_name"
            ),
            "company_reg_date": record.get(
                "company_reg_date"
            ),
            "company_status": record.get(
                "company_status"
            ),
            "company_type": record.get(
                "company_type"
            ),
            "address": record.get(
                "address"
            ),
            "eircode": record.get(
                "eircode"
            ),
            "nace_v2_code": record.get(
                "nace_v2_code"
            ),
            "princ_object_code": record.get(
                "princ_object_code"
            ),
        }

    def process_incremental_records(
        self,
        records: list[dict[str, Any]],
    ) -> tuple[list[Any], dict[str, int]]:

        counts = {
            "NEW": 0,
            "UNCHANGED": 0,
            "CHANGED": 0,
            "INVALID": 0,
        }

        companies: list[Any] = []

        for record in records:

            company_number = record.get(
                "company_num"
            )

            if company_number in (
                None,
                "",
            ):
                counts["INVALID"] += 1
                continue

            state_record = self._state_record(
                record
            )

            classification = (
                self.state.classify_record(
                    state_record,
                    source=CRO_SOURCE,
                )
            )

            counts[classification] += 1

            if classification in (
                "NEW",
                "CHANGED",
            ):

                self.state.record_seen(
                    state_record,
                    source=CRO_SOURCE,
                )

                companies.append(
                    record
                )

        return companies, counts

    def close(self) -> None:
        connection = getattr(
            self.state,
            "_connection",
            None,
        )

        if connection is None:
            connection = getattr(
                self.state,
                "_conn",
                None,
            )

        if connection is not None:
            connection.close()


# ======================================================================
# TEST DATA
# ======================================================================


def build_records() -> list[dict[str, Any]]:
    return [
        {
            "company_num": 100001,
            "company_name": (
                "ESSEMVEE TEST ONE LIMITED"
            ),
            "company_reg_date": (
                "2026-08-28T00:00:00"
            ),
            "company_status": "Normal",
            "company_type": (
                "Private limited by shares"
            ),
            "address": "Dublin",
            "eircode": "D01TEST",
            "nace_v2_code": "6201",
            "princ_object_code": "62.01",
        },
        {
            "company_num": 100002,
            "company_name": (
                "ESSEMVEE TEST TWO LIMITED"
            ),
            "company_reg_date": (
                "2026-08-28T00:00:00"
            ),
            "company_status": "Normal",
            "company_type": (
                "Private limited by shares"
            ),
            "address": "Cork",
            "eircode": "T12TEST",
            "nace_v2_code": "6201",
            "princ_object_code": "62.01",
        },
        {
            "company_num": 100003,
            "company_name": (
                "ESSEMVEE TEST THREE LIMITED"
            ),
            "company_reg_date": (
                "2026-08-28T00:00:00"
            ),
            "company_status": "Normal",
            "company_type": (
                "Private limited by shares"
            ),
            "address": "Galway",
            "eircode": "H91TEST",
            "nace_v2_code": "6201",
            "princ_object_code": "62.01",
        },
    ]


# ======================================================================
# CLEANUP
# ======================================================================


def close_connection(
    store: Any,
) -> None:

    connection = getattr(
        store,
        "_connection",
        None,
    )

    if connection is None:
        connection = getattr(
            store,
            "_conn",
            None,
        )

    if connection is not None:
        connection.close()


# ======================================================================
# TEST SUITE
# ======================================================================


def main() -> None:

    print()
    print("=" * 60)
    print("              CRO SCANNER TEST SUITE")
    print("=" * 60)

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix="essemvee_cro_scanner_test_"
        )
    )

    fake_cro: FakeCRO | None = None
    scan_state: RegistryScanStateStore | None = None

    try:

        company_state_db = (
            temp_dir / "company_state.sqlite3"
        )

        scan_state_db = (
            temp_dir / "scan_state.sqlite3"
        )

        fake_cro = FakeCRO(
            records=build_records(),
            state_db_path=company_state_db,
        )

        scan_state = RegistryScanStateStore(
            scan_state_db
        )

        scanner = CROScanner(
            cro=fake_cro,
            scan_state=scan_state,
        )

        # ==============================================================
        # TEST 1
        # ==============================================================

        print()
        print("=" * 60)
        print("TEST 1: First scan")

        result = scanner.scan(
            batch_size=2,
            max_batches=1,
            reset=True,
        )

        print(
            f"Batches: "
            f"{result.batches_processed}"
        )

        print(
            f"Records: "
            f"{result.records_processed}"
        )

        print(
            f"NEW: "
            f"{result.new_records}"
        )

        print(
            f"Companies for processing: "
            f"{result.companies_for_processing}"
        )

        assert (
            result.batches_processed == 1
        )

        assert (
            result.records_processed == 2
        )

        assert (
            result.new_records == 2
        )

        assert (
            result.changed_records == 0
        )

        assert (
            result.unchanged_records == 0
        )

        assert (
            result.companies_for_processing == 2
        )

        print("PASS")

        # ==============================================================
        # TEST 2
        # ==============================================================

        print()
        print("=" * 60)
        print(
            "TEST 2: Resume from saved offset"
        )

        result = scanner.scan(
            batch_size=2,
            max_batches=1,
            reset=False,
        )

        print(
            f"Started offset: "
            f"{result.started_offset}"
        )

        print(
            f"Final offset: "
            f"{result.final_offset}"
        )

        print(
            f"NEW: "
            f"{result.new_records}"
        )

        print(
            f"Companies for processing: "
            f"{result.companies_for_processing}"
        )

        assert (
            result.started_offset == 2
        )

        assert (
            result.final_offset == 3
        )

        assert (
            result.records_processed == 1
        )

        assert (
            result.new_records == 1
        )

        assert (
            result.companies_for_processing == 1
        )

        print("PASS")

        # ==============================================================
        # TEST 3
        # ==============================================================

        print()
        print("=" * 60)
        print(
            "TEST 3: Re-scan after dataset exhaustion"
        )

        result = scanner.scan(
            batch_size=2,
            max_batches=1,
            reset=False,
        )

        print(
            f"Started offset: "
            f"{result.started_offset}"
        )

        print(
            f"Final offset: "
            f"{result.final_offset}"
        )

        print(
            f"Records: "
            f"{result.records_processed}"
        )

        print(
            f"Companies for processing: "
            f"{result.companies_for_processing}"
        )

        assert (
            result.started_offset == 3
        )

        assert (
            result.records_processed == 0
        )

        assert (
            result.new_records == 0
        )

        assert (
            result.changed_records == 0
        )

        assert (
            result.unchanged_records == 0
        )

        assert (
            result.companies_for_processing == 0
        )

        print("PASS")

        # ==============================================================
        # TEST 4
        # ==============================================================

        print()
        print("=" * 60)
        print(
            "TEST 4: Scan state persistence"
        )

        state = scan_state.get(
            CRO_SOURCE
        )

        assert state is not None

        print(
            f"Status: "
            f"{state['status']}"
        )

        print(
            f"Current offset: "
            f"{state['current_offset']}"
        )

        print(
            f"Records processed: "
            f"{state['records_processed']}"
        )

        assert (
            state["status"] == "COMPLETED"
        )

        assert (
            state["current_offset"] == 3
        )

        assert (
            state["records_processed"] == 3
        )

        print("PASS")

        # ==============================================================
        # FINAL
        # ==============================================================

        print()
        print("=" * 60)
        print(
            "ALL CRO SCANNER TESTS PASSED"
        )
        print("=" * 60)

    finally:

        if fake_cro is not None:
            try:
                fake_cro.close()
            except Exception:
                pass

        if scan_state is not None:
            try:
                close_connection(
                    scan_state
                )
            except Exception:
                pass

        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )


if __name__ == "__main__":
    main()