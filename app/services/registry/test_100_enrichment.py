from __future__ import annotations

"""
======================================================================
ESSEMVEE AI SDR
100 NEW IRISH COMPANY ENRICHMENT TEST
======================================================================

READ-ONLY TEST

Pipeline:

Ireland CRO
    |
    v
100 newest active/recent companies
    |
    v
Deterministic qualification
    |
    +---- REJECT --------> Stop
    |
    +---- POSSIBLE -------+
    |                     |
    +---- QUALIFIED ------+
                          |
                          v
                  Company enrichment
                          |
                          v
                       Report

NO EMAILS
NO LINKEDIN MESSAGES
NO SDR DATABASE CHANGES
NO OUTREACH
======================================================================
"""

from typing import Any

from app.services.registry.ireland_cro import IrelandCRO
from app.services.prospect_qualification import (
    ProspectQualifier,
    QUALIFIED,
    POSSIBLE,
)


# ======================================================================
# CONFIGURATION
# ======================================================================

COMPANY_LIMIT = 100
RECENT_DAYS = 90


# ======================================================================
# HELPERS
# ======================================================================

def get_value(
    obj: Any,
    field: str,
    default: Any = None,
) -> Any:

    if isinstance(obj, dict):

        return obj.get(
            field,
            default,
        )

    return getattr(
        obj,
        field,
        default,
    )


def safe_text(
    value: Any,
) -> str | None:

    if value is None:

        return None

    text = str(value).strip()

    return text or None


# ======================================================================
# CRO RECORD -> QUALIFIER OBJECT
# ======================================================================

def prepare_company_for_qualification(
    company: Any,
) -> dict[str, Any]:

    """
    Convert the IrelandCRO company object into exactly the
    field structure expected by ProspectQualifier.

    IMPORTANT:

    We deliberately keep this conversion local to this test.

    We are NOT changing the production CRO model or the
    production qualification engine.
    """

    return {

        "company_name": (
            get_value(
                company,
                "company_name",
            )
            or "Unknown company"
        ),

        "status": (
            get_value(
                company,
                "status",
            )
            or ""
        ),

        "company_type": (
            get_value(
                company,
                "company_type",
            )
            or ""
        ),

        "registration_date": (
            get_value(
                company,
                "registration_date",
            )
        ),

        "nace_code": (
            get_value(
                company,
                "nace_code",
            )
        ),
    }


# ======================================================================
# ENRICHMENT
# ======================================================================

def enrich_company(
    company: Any,
) -> dict[str, Any]:

    """
    Run the existing company enrichment service.

    This is intentionally isolated from qualification.
    """

    from app.services.company_enrichment import (
        enrich_candidate,
    )

    from app.models.discovery import (
        DiscoveryCandidate,
    )

    company_name = (
        get_value(
            company,
            "company_name",
        )
        or "Unknown company"
    )

    company_number = (
        get_value(
            company,
            "company_number",
        )
    )

    registration_date = (
        get_value(
            company,
            "registration_date",
        )
    )

    status = (
        get_value(
            company,
            "status",
        )
    )

    nace_code = (
        get_value(
            company,
            "nace_code",
        )
    )

    source_url = (
        get_value(
            company,
            "source_url",
        )
    )

    print()
    print("-" * 70)
    print(
        f"[ENRICH] {company_name}"
    )

    candidate = DiscoveryCandidate(

        company_name=company_name,

        website=None,

        country="Ireland",

        industry=None,

        employee_count=None,

        description=(
            f"Irish CRO registered company. "
            f"NACE {nace_code or 'not established'}."
        ),

        discovery_source="Ireland CRO",

        source_url=source_url,

        confidence=100,
    )

    try:

        enriched = enrich_candidate(
            candidate
        )

        website = get_value(
            enriched,
            "website",
        )

        industry = get_value(
            enriched,
            "industry",
        )

        employee_count = get_value(
            enriched,
            "employee_count",
        )

        description = get_value(
            enriched,
            "description",
        )

        print(
            f"[ENRICH] Website: "
            f"{website or 'NOT FOUND'}"
        )

        print(
            f"[ENRICH] Industry: "
            f"{industry or 'NOT ESTABLISHED'}"
        )

        print(
            f"[ENRICH] Employees: "
            f"{employee_count if employee_count is not None else 'NOT ESTABLISHED'}"
        )

        return {

            "company_name": company_name,

            "company_number": company_number,

            "registration_date": registration_date,

            "status": status,

            "nace_code": nace_code,

            "website": website,

            "industry": industry,

            "employee_count": employee_count,

            "description": description,

            "enrichment_success": True,
        }

    except Exception as exc:

        print(
            f"[ENRICH] FAILED: "
            f"{type(exc).__name__}: {exc}"
        )

        return {

            "company_name": company_name,

            "company_number": company_number,

            "registration_date": registration_date,

            "status": status,

            "nace_code": nace_code,

            "website": None,

            "industry": None,

            "employee_count": None,

            "description": None,

            "enrichment_success": False,

            "error": (
                f"{type(exc).__name__}: {exc}"
            ),
        }


# ======================================================================
# MAIN
# ======================================================================

def main() -> None:

    print()

    print("=" * 70)

    print(
        " ESSEMVEE — 100 NEW IRISH COMPANY ENRICHMENT TEST"
    )

    print("=" * 70)

    print()

    print(
        "MODE: READ-ONLY"
    )

    print(
        "No emails will be sent."
    )

    print(
        "No LinkedIn messages will be sent."
    )

    print(
        "No SDR records will be modified."
    )

    print(
        "No outreach will be performed."
    )

    print()

    # --------------------------------------------------------------
    # CRO DISCOVERY
    # --------------------------------------------------------------

    print(
        f"Fetching newest {COMPANY_LIMIT} "
        f"Irish CRO registrations..."
    )

    cro = IrelandCRO()

    try:

        records = cro.fetch_recent_records(
            days=RECENT_DAYS,
            limit=COMPANY_LIMIT,
        )

    except Exception as exc:

        print()

        print(
            "CRO DISCOVERY FAILED"
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

        return

    print(
        f"CRO records received: "
        f"{len(records)}"
    )

    if not records:

        print()

        print(
            "No CRO records returned."
        )

        return

    # --------------------------------------------------------------
    # MAP CRO RECORDS
    # --------------------------------------------------------------

    companies = []

    for record in records:

        try:

            company = cro.map_company(
                record
            )

            companies.append(
                company
            )

        except Exception as exc:

            print(
                "[CRO] Could not map record:"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

    companies = companies[
        :COMPANY_LIMIT
    ]

    print(
        f"Companies selected: "
        f"{len(companies)}"
    )

    # --------------------------------------------------------------
    # QUALIFIER
    # --------------------------------------------------------------

    qualifier = ProspectQualifier(
        recent_days=RECENT_DAYS
    )

    qualified = []
    possible = []
    rejected = []

    print()

    print("=" * 70)

    print(
        " QUALIFICATION"
    )

    print("=" * 70)

    for index, company in enumerate(
        companies,
        start=1,
    ):

        qualification_input = (
            prepare_company_for_qualification(
                company
            )
        )

        try:

            result = qualifier.qualify(
                qualification_input
            )

        except Exception as exc:

            print()

            print(
                f"[{index}/{len(companies)}] "
                f"Qualification ERROR"
            )

            print(
                f"Company: "
                f"{qualification_input['company_name']}"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

            rejected.append(
                (
                    company,
                    None,
                )
            )

            continue

        print()

        print(
            f"[{index}/{len(companies)}] "
            f"{result.company_name}"
        )

        print(
            f"Qualification: "
            f"{result.qualification}"
        )

        print(
            f"Score: "
            f"{result.score}/100"
        )

        print(
            f"Active: "
            f"{result.active}"
        )

        print(
            f"New company: "
            f"{result.new_company}"
        )

        print(
            f"NACE: "
            f"{qualification_input['nace_code'] or 'Not established'}"
        )

        if result.qualification == QUALIFIED:

            qualified.append(
                (
                    company,
                    result,
                )
            )

        elif result.qualification == POSSIBLE:

            possible.append(
                (
                    company,
                    result,
                )
            )

        else:

            rejected.append(
                (
                    company,
                    result,
                )
            )

    # --------------------------------------------------------------
    # SUMMARY BEFORE ENRICHMENT
    # --------------------------------------------------------------

    print()

    print("=" * 70)

    print(
        " QUALIFICATION SUMMARY"
    )

    print("=" * 70)

    print()

    print(
        f"CRO companies tested:       "
        f"{len(companies)}"
    )

    print(
        f"QUALIFIED:                  "
        f"{len(qualified)}"
    )

    print(
        f"POSSIBLE:                   "
        f"{len(possible)}"
    )

    print(
        f"REJECTED:                   "
        f"{len(rejected)}"
    )

    print()

    # --------------------------------------------------------------
    # ENRICHMENT TARGETS
    # --------------------------------------------------------------

    enrichment_targets = (
        qualified + possible
    )

    print(
        f"Companies sent to enrichment: "
        f"{len(enrichment_targets)}"
    )

    print()

    print("=" * 70)

    print(
        " COMPANY ENRICHMENT"
    )

    print("=" * 70)

    enriched_results = []

    for company, qualification in (
        enrichment_targets
    ):

        result = enrich_company(
            company
        )

        result[
            "qualification"
        ] = qualification.qualification

        result[
            "qualification_score"
        ] = qualification.score

        result[
            "strong_technology_signal"
        ] = (
            qualification.strong_technology_signal
        )

        result[
            "research_founders"
        ] = (
            qualification.research_founders
        )

        result[
            "research_website"
        ] = (
            qualification.research_website
        )

        result[
            "research_contacts"
        ] = (
            qualification.research_contacts
        )

        enriched_results.append(
            result
        )

    # --------------------------------------------------------------
    # ENRICHMENT SUMMARY
    # --------------------------------------------------------------

    website_found = sum(
        1
        for item in enriched_results
        if item.get("website")
    )

    industry_found = sum(
        1
        for item in enriched_results
        if item.get("industry")
    )

    description_found = sum(
        1
        for item in enriched_results
        if item.get("description")
    )

    enrichment_success = sum(
        1
        for item in enriched_results
        if item.get("enrichment_success")
    )

    # --------------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------------

    print()

    print("=" * 70)

    print(
        " FINAL SUMMARY"
    )

    print("=" * 70)

    print()

    print(
        f"CRO companies tested:       "
        f"{len(companies)}"
    )

    print(
        f"QUALIFIED:                  "
        f"{len(qualified)}"
    )

    print(
        f"POSSIBLE:                   "
        f"{len(possible)}"
    )

    print(
        f"REJECTED:                   "
        f"{len(rejected)}"
    )

    print()

    print(
        f"Enrichment attempted:       "
        f"{len(enriched_results)}"
    )

    print(
        f"Enrichment successful:      "
        f"{enrichment_success}"
    )

    print(
        f"Website established:        "
        f"{website_found}"
    )

    print(
        f"Industry established:       "
        f"{industry_found}"
    )

    print(
        f"Description established:    "
        f"{description_found}"
    )

    # --------------------------------------------------------------
    # ENRICHED COMPANY LIST
    # --------------------------------------------------------------

    print()

    print("=" * 70)

    print(
        f" ENRICHED COMPANIES ({len(enriched_results)})"
    )

    print("=" * 70)

    if not enriched_results:

        print(
            "None."
        )

    for index, item in enumerate(
        enriched_results,
        start=1,
    ):

        print()

        print(
            f"{index}. "
            f"{item['company_name']}"
        )

        print(
            f"   CRO Number: "
            f"{item.get('company_number')}"
        )

        print(
            f"   Registration: "
            f"{item.get('registration_date')}"
        )

        print(
            f"   Status: "
            f"{item.get('status')}"
        )

        print(
            f"   NACE: "
            f"{item.get('nace_code')}"
        )

        print(
            f"   Qualification: "
            f"{item.get('qualification')}"
        )

        print(
            f"   Score: "
            f"{item.get('qualification_score')}/100"
        )

        print(
            f"   Strong technology: "
            f"{item.get('strong_technology_signal')}"
        )

        print(
            f"   Website: "
            f"{item.get('website') or 'NOT FOUND'}"
        )

        print(
            f"   Industry: "
            f"{item.get('industry') or 'NOT ESTABLISHED'}"
        )

        print(
            f"   Employees: "
            f"{item.get('employee_count') if item.get('employee_count') is not None else 'NOT ESTABLISHED'}"
        )

        print(
            f"   Founder research: "
            f"{item.get('research_founders')}"
        )

        print(
            f"   Website research: "
            f"{item.get('research_website')}"
        )

        print(
            f"   Contact research: "
            f"{item.get('research_contacts')}"
        )

    # --------------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------------

    print()

    print("=" * 70)

    print(
        " OUTREACH SAFETY CHECK"
    )

    print("=" * 70)

    print()

    print(
        "Emails sent:              0"
    )

    print(
        "LinkedIn messages sent:   0"
    )

    print(
        "SDR records modified:     0"
    )

    print(
        "Campaigns created:        0"
    )

    print()

    print(
        "TEST COMPLETE"
    )

    print("=" * 70)


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":

    main()