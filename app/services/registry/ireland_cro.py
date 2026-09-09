from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from app.services.registry.registry_state import (
    DEFAULT_DB_PATH,
    RegistryStateStore,
)


# ============================================================
# CRO CONFIGURATION
# ============================================================

CRO_DATASTORE_URL = (
    "https://opendata.cro.ie/api/3/action/datastore_search"
)

CRO_RESOURCE_ID = (
    "3fef41bc-b8f4-4b10-8434-ce51c29b1bba"
)

CRO_SOURCE = "CRO Open Data"

CRO_SOURCE_URL = "https://opendata.cro.ie/"


# ============================================================
# NORMALIZED CRO COMPANY
# ============================================================

@dataclass
class CROCompany:
    company_number: str | None = None
    company_name: str | None = None
    registration_date: str | None = None
    status: str | None = None
    company_type: str | None = None
    address: str | None = None
    eircode: str | None = None
    nace_code: str | None = None
    principal_object_code: str | None = None
    source: str = CRO_SOURCE
    source_url: str = CRO_SOURCE_URL


# ============================================================
# IRELAND CRO
# ============================================================

class IrelandCRO:

    def __init__(
        self,
        timeout: int = 30,
        state_db_path: str | Path = DEFAULT_DB_PATH,
    ) -> None:

        self.timeout = timeout

        self.state = RegistryStateStore(
            state_db_path
        )

    # ========================================================
    # REQUEST
    # ========================================================

    def _request(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:

        response = requests.get(
            CRO_DATASTORE_URL,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise RuntimeError(
                "CRO Open Data returned "
                "an unsuccessful response."
            )

        return data

    # ========================================================
    # SCHEMA
    # ========================================================

    def get_schema(
        self,
    ) -> list[dict[str, Any]]:

        data = self._request(
            {
                "resource_id": CRO_RESOURCE_ID,
                "limit": 1,
            }
        )

        return (
            data
            .get("result", {})
            .get("fields", [])
        )

    # ========================================================
    # RAW RECORDS
    # ========================================================

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

        limit = min(
            limit,
            1000,
        )

        data = self._request(
            {
                "resource_id": CRO_RESOURCE_ID,
                "limit": limit,
                "offset": offset,
            }
        )

        return (
            data
            .get("result", {})
            .get("records", [])
        )

    # ========================================================
    # RECENT RECORDS FROM CRO
    # ========================================================

    def fetch_recent_records(
        self,
        days: int = 30,
        limit: int = 100,
    ) -> list[dict[str, Any]]:

        """
        Query CRO directly using company_reg_date.

        This avoids reading the beginning of the dataset,
        which contains historical companies.
        """

        if days < 1:
            raise ValueError(
                "days must be greater than zero."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        cutoff = (
            date.today()
            - timedelta(days=days)
        )

        cutoff_string = (
            cutoff.isoformat()
        )

        params = {
            "resource_id": CRO_RESOURCE_ID,
            "limit": min(
                limit,
                1000,
            ),
            "offset": 0,
            "filters": (
                '{"company_reg_date": '
                f'"{cutoff_string}T00:00:00"}}'
            ),
        }

        data = self._request(
            params
        )

        return (
            data
            .get("result", {})
            .get("records", [])
        )

    # ========================================================
    # FIELD HELPER
    # ========================================================

    @staticmethod
    def _value(
        record: dict[str, Any],
        field: str,
    ) -> Any:

        return record.get(
            field
        )

    # ========================================================
    # ADDRESS
    # ========================================================

    @classmethod
    def _build_address(
        cls,
        record: dict[str, Any],
    ) -> str | None:

        parts = []

        for field in [
            "company_address_1",
            "company_address_2",
            "company_address_3",
            "company_address_4",
        ]:

            value = cls._value(
                record,
                field,
            )

            if value:
                parts.append(
                    str(value).strip()
                )

        if not parts:
            return None

        return ", ".join(
            parts
        )

    # ========================================================
    # DATE NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_date(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        text = str(
            value
        ).strip()

        if not text:
            return None

        try:
            parsed = datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            )

            return parsed.date().isoformat()

        except ValueError:
            pass

        try:
            parsed = datetime.strptime(
                text,
                "%Y-%m-%d",
            )

            return parsed.date().isoformat()

        except ValueError:
            return text

    # ========================================================
    # MAP CRO RECORD
    # ========================================================

    @classmethod
    def map_company(
        cls,
        record: dict[str, Any],
    ) -> CROCompany:

        company_number = cls._value(
            record,
            "company_num",
        )

        company_name = cls._value(
            record,
            "company_name",
        )

        registration_date = (
            cls._normalize_date(
                cls._value(
                    record,
                    "company_reg_date",
                )
            )
        )

        status = cls._value(
            record,
            "company_status",
        )

        company_type = cls._value(
            record,
            "company_type",
        )

        address = cls._build_address(
            record
        )

        eircode = cls._value(
            record,
            "eircode",
        )

        nace_code = cls._value(
            record,
            "nace_v2_code",
        )

        principal_object_code = (
            cls._value(
                record,
                "princ_object_code",
            )
        )

        return CROCompany(
            company_number=(
                str(company_number)
                if company_number is not None
                else None
            ),

            company_name=(
                str(company_name).strip()
                if company_name
                else None
            ),

            registration_date=(
                registration_date
            ),

            status=(
                str(status).strip()
                if status
                else None
            ),

            company_type=(
                str(company_type).strip()
                if company_type
                else None
            ),

            address=address,

            eircode=(
                str(eircode).strip()
                if eircode
                else None
            ),

            nace_code=(
                str(nace_code).strip()
                if nace_code
                else None
            ),

            principal_object_code=(
                str(
                    principal_object_code
                ).strip()
                if principal_object_code
                else None
            ),
        )

    # ========================================================
    # REGISTRY STATE
    # ========================================================

    @staticmethod
    def _state_record(
        record: dict[str, Any],
    ) -> dict[str, Any]:

        """
        Prepare the raw CRO record for persistent state tracking.

        The CRO company number is the stable identity.
        The remaining registry fields form the observable snapshot.
        """

        company_number = record.get(
            "company_num"
        )

        if company_number is None:
            company_number = record.get(
                "company_number"
            )

        return {
            "source_record_id": (
                str(company_number).strip()
                if company_number is not None
                else None
            ),

            "company_name": (
                record.get("company_name")
            ),

            "company_reg_date": (
                record.get("company_reg_date")
            ),

            "company_status": (
                record.get("company_status")
            ),

            "company_type": (
                record.get("company_type")
            ),

            "company_address_1": (
                record.get("company_address_1")
            ),

            "company_address_2": (
                record.get("company_address_2")
            ),

            "company_address_3": (
                record.get("company_address_3")
            ),

            "company_address_4": (
                record.get("company_address_4")
            ),

            "eircode": (
                record.get("eircode")
            ),

            "nace_v2_code": (
                record.get("nace_v2_code")
            ),

            "princ_object_code": (
                record.get("princ_object_code")
            ),
        }

    def classify_record(
        self,
        record: dict[str, Any],
    ) -> str:

        """
        Classify a raw CRO record without changing state.

        Returns:

            NEW
            UNCHANGED
            CHANGED
        """

        state_record = self._state_record(
            record
        )

        return self.state.classify_record(
            state_record,
            source=CRO_SOURCE,
        )

    def record_seen(
        self,
        record: dict[str, Any],
    ) -> str:

        """
        Persist a raw CRO record and return its state.

        Returns:

            NEW
            UNCHANGED
            CHANGED
        """

        state_record = self._state_record(
            record
        )

        return self.state.record_seen(
            state_record,
            source=CRO_SOURCE,
        )

    def process_incremental_records(
        self,
        records: list[dict[str, Any]],
    ) -> tuple[
        list[CROCompany],
        dict[str, int],
    ]:

        """
        Persist and filter a batch of raw CRO records.

        Only NEW and CHANGED records are returned for downstream
        processing.

        UNCHANGED records are deliberately skipped.
        """

        companies = []

        counts = {
            "NEW": 0,
            "UNCHANGED": 0,
            "CHANGED": 0,
            "INVALID": 0,
        }

        for record in records:

            try:
                state_result = self.record_seen(
                    record
                )

            except ValueError:
                counts["INVALID"] += 1
                continue

            counts[state_result] += 1

            if state_result == "UNCHANGED":
                continue

            company = self.map_company(
                record
            )

            if not company.company_name:
                continue

            companies.append(
                company
            )

        return companies, counts

    # ========================================================
    # INCREMENTAL RECENT DISCOVERY
    # ========================================================

    def discover_recent_incremental(
        self,
        days: int = 30,
        limit: int = 100,
    ) -> tuple[
        list[CROCompany],
        dict[str, int],
    ]:

        """
        Discover recent CRO companies while using persistent state.

        First run:
            companies are classified as NEW.

        Later runs:
            unchanged companies are skipped.

        Changed registry records are returned again for processing.
        """

        records = self.fetch_recent_records(
            days=days,
            limit=limit,
        )

        companies, counts = (
            self.process_incremental_records(
                records
            )
        )

        return (
            companies,
            counts,
        )

    # ========================================================
    # FULL DATASET INCREMENTAL BATCH
    # ========================================================

    def fetch_incremental_batch(
        self,
        limit: int = 1000,
        offset: int = 0,
    ) -> tuple[
        list[CROCompany],
        dict[str, int],
    ]:

        """
        Fetch one batch from the complete CRO dataset and process
        it through persistent state.

        This is the foundation for eventually scanning the complete
        CRO dataset without repeatedly processing unchanged companies.
        """

        records = self.fetch_records(
            limit=limit,
            offset=offset,
        )

        companies, counts = (
            self.process_incremental_records(
                records
            )
        )

        return (
            companies,
            counts,
        )

    # ========================================================
    # STATE COUNTS
    # ========================================================

    def state_count(self) -> int:

        """Return the number of CRO records stored in persistent state."""

        return self.state.count(
            CRO_SOURCE
        )

    # ========================================================
    # RECENT COMPANIES
    # ========================================================

    def discover_recent(
        self,
        days: int = 30,
        limit: int = 100,
    ) -> list[CROCompany]:

        """
        Existing non-incremental recent discovery.

        This method intentionally preserves the original behavior.
        Use discover_recent_incremental() when persistent state
        filtering is required.
        """

        records = (
            self.fetch_recent_records(
                days=days,
                limit=limit,
            )
        )

        companies = []

        cutoff = (
            date.today()
            - timedelta(days=days)
        )

        for record in records:

            company = self.map_company(
                record
            )

            if not company.company_name:
                continue

            registration_date = (
                self._parse_date(
                    company.registration_date
                )
            )

            if registration_date is None:
                continue

            if registration_date < cutoff:
                continue

            # ------------------------------------------------
            # Ignore dissolved companies
            # ------------------------------------------------

            status = (
                company.status or ""
            ).lower()

            if "dissolved" in status:
                continue

            companies.append(
                company
            )

        return companies

    # ========================================================
    # DATE PARSER
    # ========================================================

    @staticmethod
    def _parse_date(
        value: str | None,
    ) -> date | None:

        if not value:
            return None

        text = str(
            value
        ).strip()

        try:
            return datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            ).date()

        except ValueError:
            pass

        for fmt in [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]:

            try:
                return datetime.strptime(
                    text,
                    fmt,
                ).date()

            except ValueError:
                continue

        return None


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    print()

    print(
        "============================================================"
    )

    print(
        "       ESSEMVEE - IRELAND CRO RECENT COMPANY TEST"
    )

    print(
        "============================================================"
    )

    cro = IrelandCRO()

    print()

    print(
        "Testing recent company discovery..."
    )

    print(
        "Window: last 30 days"
    )

    try:

        companies = (
            cro.discover_recent(
                days=30,
                limit=50,
            )
        )

        print()

        print(
            f"Recent active companies found: "
            f"{len(companies)}"
        )

        for index, company in enumerate(
            companies,
            start=1,
        ):

            print()

            print(
                f"COMPANY {index}"
            )

            print(
                f"Name: "
                f"{company.company_name}"
            )

            print(
                f"Number: "
                f"{company.company_number}"
            )

            print(
                f"Registered: "
                f"{company.registration_date}"
            )

            print(
                f"Status: "
                f"{company.status}"
            )

            print(
                f"Type: "
                f"{company.company_type}"
            )

            print(
                f"NACE: "
                f"{company.nace_code}"
            )

            print(
                f"Principal object: "
                f"{company.principal_object_code}"
            )

            print(
                f"Address: "
                f"{company.address}"
            )

            print(
                f"Eircode: "
                f"{company.eircode}"
            )

    except Exception as exc:

        print()

        print(
            "CRO TEST FAILED:"
        )

        print(
            repr(exc)
        )