from __future__ import annotations

import sqlite3

from app.services.registry.registry_state import RegistryStateStore


class InMemoryRegistryStateStore(RegistryStateStore):
    """Registry state store backed by an in-memory SQLite database."""

    def __init__(self) -> None:
        self.db_path = ":memory:"
        self._connection = sqlite3.connect(":memory:")
        self._connection.row_factory = sqlite3.Row
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        return self._connection

    def close(self) -> None:
        self._connection.close()


def main() -> None:
    store = InMemoryRegistryStateStore()

    try:
        company = {
            "company_num": "999999",
            "company_name": "ESSEMVEE TEST LIMITED",
            "company_reg_date": "2026-09-03",
            "company_status": "NORMAL",
            "nace_v2_code": "6201",
        }

        print("TEST 1: First observation")

        result = store.record_seen(
            company,
            source="ireland_cro",
        )

        print("Expected: NEW")
        print(f"Actual:   {result}")

        assert result == "NEW"

        print()
        print("TEST 2: Same company, same data")

        result = store.record_seen(
            company,
            source="ireland_cro",
        )

        print("Expected: UNCHANGED")
        print(f"Actual:   {result}")

        assert result == "UNCHANGED"

        print()
        print("TEST 3: Same company, changed data")

        changed_company = {
            **company,
            "company_status": "DISSOLVED",
        }

        result = store.record_seen(
            changed_company,
            source="ireland_cro",
        )

        print("Expected: CHANGED")
        print(f"Actual:   {result}")

        assert result == "CHANGED"

        print()
        print("TEST 4: Verify persisted record")

        saved = store.get(
            "ireland_cro",
            "999999",
        )

        assert saved is not None
        assert saved["company_name"] == "ESSEMVEE TEST LIMITED"
        assert saved["status"] == "DISSOLVED"
        assert saved["nace_code"] == "6201"
        assert saved["check_count"] == 3

        print(f"Company:     {saved['company_name']}")
        print(f"Status:      {saved['status']}")
        print(f"NACE:        {saved['nace_code']}")
        print(f"Check count: {saved['check_count']}")

        print()
        print("TEST 5: Record count")

        count = store.count("ireland_cro")

        print("Expected: 1")
        print(f"Actual:   {count}")

        assert count == 1

        print()
        print("=" * 60)
        print("ALL REGISTRY STATE TESTS PASSED")
        print("=" * 60)

    finally:
        store.close()


if __name__ == "__main__":
    main()