from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.services.registry.ireland_cro import (
    CRO_SOURCE,
    CROCompany,
    IrelandCRO,
)

from app.services.registry.registry_scan_state import (
    RegistryScanStateStore,
)


# ============================================================
# CRO SCAN RESULT
# ============================================================


@dataclass
class CROScanResult:
    """
    Summary of one CRO registry scan execution.

    companies_for_processing is the number of companies
    classified as NEW or CHANGED and returned for downstream
    processing.
    """

    source: str
    started_offset: int
    final_offset: int

    batches_processed: int
    records_processed: int

    new_records: int
    changed_records: int
    unchanged_records: int
    invalid_records: int

    companies_for_processing: int

    completed: bool


# ============================================================
# CRO SCANNER
# ============================================================


class CROScanner:
    """
    Persistent incremental scanner for the Ireland CRO dataset.

    Dataset-level state:
        RegistryScanStateStore

    Company-level state:
        RegistryStateStore through IrelandCRO

    Lifecycle:

        NEW
          |
          v
        RUNNING
          |
          +----> FAILED ----> resume
          |
          +----> COMPLETED
                         |
                         v
                    new full scan
                    from offset 0

    Company records are independently classified as:

        NEW
        CHANGED
        UNCHANGED
        INVALID

    Only NEW and CHANGED companies are returned to downstream
    processing.
    """

    def __init__(
        self,
        cro: IrelandCRO | None = None,
        scan_state: RegistryScanStateStore | None = None,
        scan_state_db_path: str | Path | None = None,
    ) -> None:

        # ----------------------------------------------------
        # CRO adapter
        # ----------------------------------------------------

        if cro is not None:
            self.cro = cro

        elif scan_state_db_path is not None:
            self.cro = IrelandCRO(
                state_db_path=scan_state_db_path
            )

        else:
            # IMPORTANT:
            # Never pass None to IrelandCRO.
            # Let IrelandCRO use its own default database path.
            self.cro = IrelandCRO()

        # ----------------------------------------------------
        # Dataset-level scan state
        # ----------------------------------------------------

        if scan_state is not None:
            self.scan_state = scan_state

        elif scan_state_db_path is not None:
            self.scan_state = RegistryScanStateStore(
                scan_state_db_path
            )

        else:
            self.scan_state = RegistryScanStateStore()

        self.source = CRO_SOURCE

    # ========================================================
    # STATE
    # ========================================================

    def get_state(self) -> dict[str, Any] | None:
        """
        Return the persistent dataset-level scan state.
        """

        return self.scan_state.get(
            self.source
        )

    # ========================================================
    # PREPARE SCAN
    # ========================================================

    def prepare_scan(
        self,
        batch_size: int = 1000,
        reset: bool = False,
    ) -> dict[str, Any]:
        """
        Prepare a scan according to the persisted lifecycle.

        Behavior:

        No state:
            Start at offset 0.

        RUNNING:
            Resume the existing offset.

        FAILED:
            Resume the existing offset.

        COMPLETED:
            Start a completely new dataset pass at offset 0.

        RESET:
            Start from offset 0.

        reset=True:
            Force a new scan from offset 0.
        """

        if batch_size < 1:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        existing = self.get_state()

        # ----------------------------------------------------
        # First scan
        # ----------------------------------------------------

        if existing is None:
            return self.scan_state.start_scan(
                self.source,
                batch_size=batch_size,
            )

        status = existing["status"]

        # ----------------------------------------------------
        # Explicit reset
        # ----------------------------------------------------

        if reset:
            self.scan_state.reset_scan(
                self.source,
                batch_size=batch_size,
            )

            return self.scan_state.start_scan(
                self.source,
                batch_size=batch_size,
            )

        # ----------------------------------------------------
        # RUNNING
        #
        # Preserve current offset.
        # ----------------------------------------------------

        if status == "RUNNING":
            return self.scan_state.start_scan(
                self.source,
                batch_size=batch_size,
            )

        # ----------------------------------------------------
        # FAILED
        #
        # Preserve current offset.
        # ----------------------------------------------------

        if status == "FAILED":
            return self.scan_state.start_scan(
                self.source,
                batch_size=batch_size,
            )

        # ----------------------------------------------------
        # COMPLETED
        #
        # A completed scan is a finished dataset pass.
        #
        # The next scan must begin at offset 0 so the current
        # registry snapshot can be compared against persisted
        # company state.
        #
        # Existing companies will normally classify as
        # UNCHANGED and therefore will not be sent downstream.
        # ----------------------------------------------------

        if status == "COMPLETED":
            self.scan_state.reset_scan(
                self.source,
                batch_size=batch_size,
            )

            return self.scan_state.start_scan(
                self.source,
                batch_size=batch_size,
            )

        # ----------------------------------------------------
        # RESET
        # ----------------------------------------------------

        if status == "RESET":
            return self.scan_state.start_scan(
                self.source,
                batch_size=batch_size,
            )

        raise ValueError(
            f"Unsupported scan state status: {status}"
        )

    # ========================================================
    # PROCESS ONE BATCH
    # ========================================================

    def process_batch(
        self,
        offset: int,
        batch_size: int,
        on_companies: Callable[
            [list[CROCompany]],
            None,
        ]
        | None = None,
    ) -> dict[str, Any]:
        """
        Fetch and process one CRO batch.

        The batch is considered successful only after company
        state processing completes and scan-level state is
        persisted.
        """

        if offset < 0:
            raise ValueError(
                "offset cannot be negative."
            )

        if batch_size < 1:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        # ----------------------------------------------------
        # Mark batch start
        # ----------------------------------------------------

        self.scan_state.start_batch(
            self.source
        )

        # ----------------------------------------------------
        # Fetch records
        # ----------------------------------------------------

        records = self.cro.fetch_records(
            limit=batch_size,
            offset=offset,
        )

        # ----------------------------------------------------
        # Dataset exhausted
        # ----------------------------------------------------

        if not records:
            return {
                "records": 0,
                "counts": {
                    "NEW": 0,
                    "UNCHANGED": 0,
                    "CHANGED": 0,
                    "INVALID": 0,
                },
                "companies": [],
                "next_offset": offset,
                "end_of_dataset": True,
            }

        # ----------------------------------------------------
        # Incremental company-level processing
        # ----------------------------------------------------

        companies, counts = (
            self.cro.process_incremental_records(
                records
            )
        )

        records_processed = len(records)

        next_offset = (
            offset + records_processed
        )

        # ----------------------------------------------------
        # Persist successful batch
        # ----------------------------------------------------

        self.scan_state.complete_batch(
            source=self.source,
            records_processed=records_processed,
            records_new=counts.get(
                "NEW",
                0,
            ),
            records_changed=counts.get(
                "CHANGED",
                0,
            ),
            records_unchanged=counts.get(
                "UNCHANGED",
                0,
            ),
            records_invalid=counts.get(
                "INVALID",
                0,
            ),
            next_offset=next_offset,
        )

        # ----------------------------------------------------
        # Downstream callback
        #
        # Only NEW / CHANGED companies are supplied by the CRO
        # adapter.
        # ----------------------------------------------------

        if (
            companies
            and on_companies is not None
        ):
            on_companies(companies)

        return {
            "records": records_processed,
            "counts": counts,
            "companies": companies,
            "next_offset": next_offset,
            "end_of_dataset": False,
        }

    # ========================================================
    # SCAN
    # ========================================================

    def scan(
        self,
        batch_size: int = 1000,
        max_batches: int | None = None,
        reset: bool = False,
        on_companies: Callable[
            [list[CROCompany]],
            None,
        ]
        | None = None,
    ) -> CROScanResult:
        """
        Execute a resumable CRO scan.

        max_batches is useful for controlled testing or
        intentionally chunked execution.

        If max_batches is reached, the scan remains RUNNING and
        the saved offset is preserved.

        If the CRO dataset is exhausted, the scan becomes
        COMPLETED.

        If an exception occurs, the scan becomes FAILED while
        preserving the last successfully committed offset.
        """

        if batch_size < 1:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        if (
            max_batches is not None
            and max_batches < 1
        ):
            raise ValueError(
                "max_batches must be greater than zero."
            )

        # ----------------------------------------------------
        # Prepare lifecycle
        # ----------------------------------------------------

        state = self.prepare_scan(
            batch_size=batch_size,
            reset=reset,
        )

        started_offset = int(
            state["current_offset"]
        )

        current_offset = started_offset

        batches_processed = 0
        records_processed = 0

        new_records = 0
        changed_records = 0
        unchanged_records = 0
        invalid_records = 0

        companies_for_processing = 0

        try:

            while True:

                # ------------------------------------------------
                # Controlled execution boundary
                # ------------------------------------------------

                if (
                    max_batches is not None
                    and batches_processed
                    >= max_batches
                ):
                    break

                # ------------------------------------------------
                # Process batch
                # ------------------------------------------------

                batch_result = (
                    self.process_batch(
                        offset=current_offset,
                        batch_size=batch_size,
                        on_companies=on_companies,
                    )
                )

                # ------------------------------------------------
                # Dataset exhausted
                # ------------------------------------------------

                if batch_result[
                    "end_of_dataset"
                ]:

                    self.scan_state.complete_scan(
                        self.source
                    )

                    final_state = (
                        self.scan_state.get(
                            self.source
                        )
                    )

                    final_offset = int(
                        final_state[
                            "current_offset"
                        ]
                    )

                    return CROScanResult(
                        source=self.source,
                        started_offset=started_offset,
                        final_offset=final_offset,
                        batches_processed=(
                            batches_processed
                        ),
                        records_processed=(
                            records_processed
                        ),
                        new_records=new_records,
                        changed_records=(
                            changed_records
                        ),
                        unchanged_records=(
                            unchanged_records
                        ),
                        invalid_records=(
                            invalid_records
                        ),
                        companies_for_processing=(
                            companies_for_processing
                        ),
                        completed=True,
                    )

                # ------------------------------------------------
                # Aggregate statistics
                # ------------------------------------------------

                batch_counts = (
                    batch_result["counts"]
                )

                batch_records = int(
                    batch_result["records"]
                )

                batch_companies = (
                    batch_result["companies"]
                )

                batches_processed += 1

                records_processed += (
                    batch_records
                )

                new_records += int(
                    batch_counts.get(
                        "NEW",
                        0,
                    )
                )

                changed_records += int(
                    batch_counts.get(
                        "CHANGED",
                        0,
                    )
                )

                unchanged_records += int(
                    batch_counts.get(
                        "UNCHANGED",
                        0,
                    )
                )

                invalid_records += int(
                    batch_counts.get(
                        "INVALID",
                        0,
                    )
                )

                # Count actual companies returned by
                # company-level incremental processing.
                companies_for_processing += len(
                    batch_companies
                )

                current_offset = int(
                    batch_result[
                        "next_offset"
                    ]
                )

        except Exception as exc:

            # ----------------------------------------------------
            # Preserve failure state.
            #
            # The last successful batch has already committed its
            # offset. Therefore a retry resumes safely from that
            # position.
            # ----------------------------------------------------

            try:
                self.scan_state.fail_scan(
                    self.source,
                    str(exc),
                )
            except Exception:
                # Preserve the original exception.
                pass

            raise

        # --------------------------------------------------------
        # max_batches reached.
        #
        # Leave state RUNNING so the next scan resumes from the
        # persisted offset.
        # --------------------------------------------------------

        final_state = self.scan_state.get(
            self.source
        )

        final_offset = int(
            final_state["current_offset"]
        )

        return CROScanResult(
            source=self.source,
            started_offset=started_offset,
            final_offset=final_offset,
            batches_processed=batches_processed,
            records_processed=records_processed,
            new_records=new_records,
            changed_records=changed_records,
            unchanged_records=unchanged_records,
            invalid_records=invalid_records,
            companies_for_processing=(
                companies_for_processing
            ),
            completed=False,
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self) -> None:
        """
        Close database connections when available.

        The scanner may receive test doubles, so close() is
        intentionally defensive.
        """

        scan_close = getattr(
            self.scan_state,
            "close",
            None,
        )

        if callable(scan_close):
            scan_close()

        cro_close = getattr(
            self.cro,
            "close",
            None,
        )

        if callable(cro_close):
            cro_close()


# ============================================================
# CLI
# ============================================================


if __name__ == "__main__":

    scanner = CROScanner()

    try:

        result = scanner.scan(
            batch_size=1000,
            max_batches=1,
        )

        print("=" * 60)
        print("CRO SCANNER")
        print("=" * 60)

        print(
            f"Started offset: "
            f"{result.started_offset}"
        )

        print(
            f"Final offset: "
            f"{result.final_offset}"
        )

        print(
            f"Batches processed: "
            f"{result.batches_processed}"
        )

        print(
            f"Records processed: "
            f"{result.records_processed}"
        )

        print(
            f"NEW: "
            f"{result.new_records}"
        )

        print(
            f"CHANGED: "
            f"{result.changed_records}"
        )

        print(
            f"UNCHANGED: "
            f"{result.unchanged_records}"
        )

        print(
            f"INVALID: "
            f"{result.invalid_records}"
        )

        print(
            f"Companies for processing: "
            f"{result.companies_for_processing}"
        )

        print(
            f"Completed: "
            f"{result.completed}"
        )

    finally:
        scanner.close()