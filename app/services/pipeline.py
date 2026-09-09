from app.agents.scout import scout_company

from app.models.discovery import (
    DiscoveryCandidate,
)

from app.models.lead import (
    CompanyInput,
    CompanySignal,
)

from app.models.outreach import (
    OutreachBrief,
)

from app.models.signal import (
    Signal,
)

from app.services.company_enrichment import (
    enrich_candidate,
)

from app.services.evidence_verifier import (
    verify_hiring_signal,
)

from app.services.outreach import (
    build_outreach_brief,
)


def convert_signals(
    signals: list[Signal],
    candidate: DiscoveryCandidate,
) -> list[CompanySignal]:
    """
    Convert extracted Signal objects into CompanySignal objects.

    Hiring signals are independently checked against the company's
    official website.

    Verification levels:

    EXACT_JOB_VERIFIED
        Official company website exposes the exact job.

    CAREERS_CONFIRMED
        Official company careers/open-roles page is confirmed,
        but the exact job is not exposed in static HTML.

    EXTERNAL_ONLY
        Hiring evidence exists externally, but the official
        company careers page could not independently confirm it.

    NOT_VERIFIED
        No verification was established.
    """

    converted: list[CompanySignal] = []

    for signal in signals:

        # --------------------------------------------------
        # Default verification state
        # --------------------------------------------------

        verification_level = (
            "NOT_VERIFIED"
        )

        official_careers_found = False

        exact_job_verified = False

        careers_url = None

        officially_verified = False

        # --------------------------------------------------
        # Hiring verification
        # --------------------------------------------------

        if (
            signal.signal_type == "Hiring"
            and candidate.website
        ):

            print()

            print(
                f"[DEBUG] Running official verification "
                f"for {candidate.company_name}"
            )

            verification = (
                verify_hiring_signal(
                    company_name=(
                        candidate.company_name
                    ),
                    website=(
                        candidate.website
                    ),
                    title=signal.title,
                    description=(
                        signal.description
                    ),
                )
            )

            official_careers_found = (
                verification.official_careers_found
            )

            exact_job_verified = (
                verification.exact_job_verified
            )

            careers_url = (
                verification.careers_url
            )

            verification_level = (
                verification.verification_level
            )

            # Only an exact job match counts as
            # officially verified.
            officially_verified = (
                exact_job_verified
            )

            print(
                "[DEBUG] Verification level: "
                f"{verification_level}"
            )

            print(
                "[DEBUG] Official careers found: "
                f"{official_careers_found}"
            )

            print(
                "[DEBUG] Exact job verified: "
                f"{exact_job_verified}"
            )

            print(
                "[DEBUG] Careers URL: "
                f"{careers_url}"
            )

        # --------------------------------------------------
        # Build CompanySignal
        # --------------------------------------------------

        converted.append(
            CompanySignal(
                signal_type=(
                    signal.signal_type
                ),

                description=(
                    signal.description
                ),

                discovery_source=(
                    signal.discovery_source
                ),

                source=signal.source,

                source_url=(
                    signal.source_url
                ),

                source_trust=(
                    signal.source_trust
                ),

                strength=signal.strength,

                officially_verified=(
                    officially_verified
                ),

                verification_level=(
                    verification_level
                ),

                official_careers_found=(
                    official_careers_found
                ),

                exact_job_verified=(
                    exact_job_verified
                ),

                careers_url=(
                    careers_url
                ),
            )
        )

    return converted


def enrich_company(
    candidate: DiscoveryCandidate,
) -> DiscoveryCandidate:
    """
    Enrich a discovered company with additional
    company information.
    """

    return enrich_candidate(
        candidate
    )


def build_company_input(
    candidate: DiscoveryCandidate,
    signals: list[Signal],
) -> CompanyInput:
    """
    Build the CompanyInput consumed by the
    Scout Agent.
    """

    return CompanyInput(
        company_name=(
            candidate.company_name
        ),

        website=candidate.website,

        country=candidate.country,

        industry=candidate.industry,

        employee_count=(
            candidate.employee_count
        ),

        description=(
            candidate.description
        ),

        signals=convert_signals(
            signals,
            candidate,
        ),
    )


def analyze_candidate(
    candidate: DiscoveryCandidate,
    signals: list[Signal],
):
    """
    Existing Scout pipeline.

    Returns:
        ScoutResult

    This function intentionally keeps its existing
    return contract so existing callers are not broken.
    """

    print()

    print(
        f"[DEBUG] Enriching candidate: "
        f"{candidate.company_name}"
    )

    candidate = enrich_company(
        candidate
    )

    print(
        f"[DEBUG] Enriched industry: "
        f"{candidate.industry}"
    )

    print(
        f"[DEBUG] Enriched employees: "
        f"{candidate.employee_count}"
    )

    print(
        f"[DEBUG] Enriched description: "
        f"{candidate.description}"
    )

    company = build_company_input(
        candidate,
        signals,
    )

    return scout_company(
        company
    )


def analyze_candidate_with_outreach(
    candidate: DiscoveryCandidate,
    signals: list[Signal],
) -> tuple[
    CompanyInput,
    object,
    OutreachBrief,
]:
    """
    Run the complete Scout + Outreach pipeline.

    Returns:

        CompanyInput
            The enriched company and verified signals.

        ScoutResult
            Deterministic scoring plus AI sales intelligence.

        OutreachBrief
            Structured sales-ready intelligence derived
            from the same evidence and Scout result.

    The existing analyze_candidate() function remains
    unchanged so existing callers continue to work.
    """

    print()

    print(
        f"[DEBUG] Enriching candidate: "
        f"{candidate.company_name}"
    )

    candidate = enrich_company(
        candidate
    )

    print(
        f"[DEBUG] Enriched industry: "
        f"{candidate.industry}"
    )

    print(
        f"[DEBUG] Enriched employees: "
        f"{candidate.employee_count}"
    )

    print(
        f"[DEBUG] Enriched description: "
        f"{candidate.description}"
    )

    # --------------------------------------------------
    # Build the exact CompanyInput used by Scout
    # --------------------------------------------------

    company = build_company_input(
        candidate,
        signals,
    )

    # --------------------------------------------------
    # Run Scout
    # --------------------------------------------------

    result = scout_company(
        company
    )

    # --------------------------------------------------
    # Build OutreachBrief from the same evidence
    # --------------------------------------------------

    print()

    print(
        f"[DEBUG] Building outreach brief "
        f"for {candidate.company_name}"
    )

    outreach_brief = (
        build_outreach_brief(
            company=company,
            result=result,
        )
    )

    print(
        "[DEBUG] Outreach brief created"
    )

    return (
        company,
        result,
        outreach_brief,
    )