from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from app.services.registry.ireland_cro import IrelandCRO
from app.services.prospect_qualification import ProspectQualifier


# ============================================================
# ESSEMVEE — TEST 100 NEWLY REGISTERED IRISH COMPANIES
# ============================================================
#
# Purpose:
#
#   CRO
#    ↓
#   100 newly registered companies
#    ↓
#   Active validation
#    ↓
#   NACE qualification
#    ↓
#   ESSEMVEE qualification
#
# This is a TEST ONLY.
#
# It does NOT:
#
# - modify the database
# - modify existing prospects
# - contact companies
# - send email
# - research people
# - call LinkedIn
# - call Apollo/Cognism/Lusha/Kaspr
#
# ============================================================


TEST_COMPANY_COUNT = 100

# Look back far enough to obtain at least 100 records.
# We then select the 100 most recent registration records.
LOOKBACK_DAYS = 90


def main() -> None:

    print()

    print(
        "=" * 70
    )

    print(
        " ESSEMVEE — 100 NEW IRISH COMPANY QUALIFICATION TEST"
    )

    print(
        "=" * 70
    )

    print()

    cro = IrelandCRO()

    qualifier = ProspectQualifier(
        recent_days=90
    )

    # --------------------------------------------------------
    # 1. Fetch recent CRO records
    # --------------------------------------------------------

    print(
        f"Fetching newly registered companies "
        f"from the last {LOOKBACK_DAYS} days..."
    )

    records = cro.fetch_recent_records(
        days=LOOKBACK_DAYS,
        limit=1000,
    )

    print(
        f"CRO records received: {len(records)}"
    )

    # --------------------------------------------------------
    # 2. Convert to normalized companies
    # --------------------------------------------------------

    companies = []

    for record in records:

        company = cro.map_company(
            record
        )

        if not company.company_name:
            continue

        if not company.registration_date:
            continue

        companies.append(
            company
        )

    # --------------------------------------------------------
    # 3. Sort newest first
    # --------------------------------------------------------

    companies.sort(
        key=lambda company: (
            company.registration_date or ""
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # 4. Select exactly 100
    # --------------------------------------------------------

    companies = companies[
        :TEST_COMPANY_COUNT
    ]

    print(
        f"Companies selected for test: "
        f"{len(companies)}"
    )

    if len(companies) < TEST_COMPANY_COUNT:

        print()

        print(
            "WARNING:"
        )

        print(
            f"Only {len(companies)} companies were "
            f"available in the requested window."
        )

        print(
            "The test will continue with the available records."
        )

    # --------------------------------------------------------
    # 5. Counters
    # --------------------------------------------------------

    qualification_counts = Counter()

    active_count = 0
    inactive_count = 0

    relevant_nace_count = 0
    strong_technology_count = 0
    new_company_count = 0

    qualified_companies = []
    possible_companies = []
    rejected_companies = []

    # --------------------------------------------------------
    # 6. Run qualification
    # --------------------------------------------------------

    print()

    print(
        "=" * 70
    )

    print(
        " QUALIFICATION RESULTS"
    )

    print(
        "=" * 70
    )

    for index, company in enumerate(
        companies,
        start=1,
    ):

        result = qualifier.qualify(
            company
        )

        qualification_counts[
            result.qualification
        ] += 1

        if result.active:
            active_count += 1
        else:
            inactive_count += 1

        if result.relevant_nace:
            relevant_nace_count += 1

        if result.strong_technology_signal:
            strong_technology_count += 1

        if result.new_company:
            new_company_count += 1

        if result.qualification == "QUALIFIED":

            qualified_companies.append(
                (
                    company,
                    result,
                )
            )

        elif result.qualification == "POSSIBLE":

            possible_companies.append(
                (
                    company,
                    result,
                )
            )

        else:

            rejected_companies.append(
                (
                    company,
                    result,
                )
            )

        # ----------------------------------------------------
        # Print every company
        # ----------------------------------------------------

        print()

        print(
            f"[{index:03d}] "
            f"{company.company_name}"
        )

        print(
            f"      Number: "
            f"{company.company_number}"
        )

        print(
            f"      Registered: "
            f"{company.registration_date}"
        )

        print(
            f"      Status: "
            f"{company.status}"
        )

        print(
            f"      NACE: "
            f"{company.nace_code or 'NOT ESTABLISHED'}"
        )

        print(
            f"      Qualification: "
            f"{result.qualification}"
        )

        print(
            f"      Score: "
            f"{result.score}/100"
        )

    # --------------------------------------------------------
    # 7. Summary
    # --------------------------------------------------------

    total = len(companies)

    print()

    print(
        "=" * 70
    )

    print(
        " SUMMARY"
    )

    print(
        "=" * 70
    )

    print()

    print(
        f"CRO companies tested:       {total}"
    )

    print(
        f"Active:                     {active_count}"
    )

    print(
        f"Inactive:                   {inactive_count}"
    )

    print(
        f"New companies:              {new_company_count}"
    )

    print(
        f"Relevant NACE:              {relevant_nace_count}"
    )

    print(
        f"Strong technology NACE:     {strong_technology_count}"
    )

    print()

    qualified = qualification_counts[
        "QUALIFIED"
    ]

    possible = qualification_counts[
        "POSSIBLE"
    ]

    rejected = qualification_counts[
        "REJECT"
    ]

    print(
        f"QUALIFIED:                  {qualified}"
    )

    print(
        f"POSSIBLE:                   {possible}"
    )

    print(
        f"REJECTED:                   {rejected}"
    )

    # --------------------------------------------------------
    # Qualification rate
    # --------------------------------------------------------

    if total:

        qualification_rate = (
            qualified
            / total
        ) * 100

        research_rate = (
            (
                qualified
                + possible
            )
            / total
        ) * 100

        print()

        print(
            f"Qualification rate:         "
            f"{qualification_rate:.1f}%"
        )

        print(
            f"Research candidate rate:    "
            f"{research_rate:.1f}%"
        )

    # --------------------------------------------------------
    # 8. Qualified companies
    # --------------------------------------------------------

    print()

    print(
        "=" * 70
    )

    print(
        f" QUALIFIED COMPANIES ({qualified})"
    )

    print(
        "=" * 70
    )

    if not qualified_companies:

        print(
            "None."
        )

    for company, result in qualified_companies:

        print()

        print(
            f"{company.company_name}"
        )

        print(
            f"  CRO number: "
            f"{company.company_number}"
        )

        print(
            f"  Registered: "
            f"{company.registration_date}"
        )

        print(
            f"  Status: "
            f"{company.status}"
        )

        print(
            f"  NACE: "
            f"{company.nace_code}"
        )

        print(
            f"  Score: "
            f"{result.score}/100"
        )

        print(
            "  Next action: "
            f"{result.next_action}"
        )

    # --------------------------------------------------------
    # 9. Possible companies
    # --------------------------------------------------------

    print()

    print(
        "=" * 70
    )

    print(
        f" POSSIBLE COMPANIES ({possible})"
    )

    print(
        "=" * 70
    )

    if not possible_companies:

        print(
            "None."
        )

    for company, result in possible_companies:

        print()

        print(
            f"{company.company_name}"
        )

        print(
            f"  CRO number: "
            f"{company.company_number}"
        )

        print(
            f"  Registered: "
            f"{company.registration_date}"
        )

        print(
            f"  Status: "
            f"{company.status}"
        )

        print(
            f"  NACE: "
            f"{company.nace_code}"
        )

        print(
            f"  Score: "
            f"{result.score}/100"
        )

    # --------------------------------------------------------
    # 10. NACE distribution
    # --------------------------------------------------------

    nace_counts = Counter()

    for company in companies:

        nace = (
            company.nace_code
            or "NOT ESTABLISHED"
        )

        nace_counts[nace] += 1

    print()

    print(
        "=" * 70
    )

    print(
        " NACE DISTRIBUTION"
    )

    print(
        "=" * 70
    )

    for nace, count in nace_counts.most_common():

        print(
            f"{nace:<25} {count}"
        )

    # --------------------------------------------------------
    # 11. Final recommendation
    # --------------------------------------------------------

    print()

    print(
        "=" * 70
    )

    print(
        " TEST COMPLETE"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "No companies were contacted."
    )

    print(
        "No emails were sent."
    )

    print(
        "No existing SDR records were modified."
    )

    print()

    print(
        "The results above will determine whether "
        "we should refine the NACE qualification rules "
        "before connecting CRO discovery to the live SDR pipeline."
    )

    print()


if __name__ == "__main__":

    main()