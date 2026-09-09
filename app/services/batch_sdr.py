from dataclasses import dataclass

from app.models.discovery import DiscoveryCandidate
from app.models.lead import CompanyInput, ScoutResult
from app.models.outreach import OutreachBrief
from app.models.signal import Signal

from app.services.pipeline import (
    analyze_candidate_with_outreach,
)

from app.services.prospect_discovery import (
    ProspectDiscovery,
)


@dataclass
class BatchLead:
    """
    Complete SDR intelligence package for one prospect.
    """

    candidate: DiscoveryCandidate

    company: CompanyInput

    result: ScoutResult

    outreach: OutreachBrief


PRIORITY_ORDER = {
    "HOT": 0,
    "WARM": 1,
    "WATCH": 2,
    "IGNORE": 3,
}


def _sort_key(
    lead: BatchLead,
):
    """
    Rank strongest sales opportunities first.

    Order:

    1. Opportunity score
    2. Intent score
    3. Evidence quality
    4. Priority
    """

    return (
        -lead.result.opportunity_score,
        -lead.result.intent_score,
        -lead.result.evidence_quality,
        PRIORITY_ORDER.get(
            lead.result.priority,
            99,
        ),
    )


def _get_verification_details(
    company: CompanyInput,
) -> tuple[str, bool, bool, str | None]:
    """
    Extract verification information from the
    Company's verified signals.

    Returns:

        verification_level
        official_careers_found
        exact_job_verified
        careers_url
    """

    if not company.signals:

        return (
            "NOT_VERIFIED",
            False,
            False,
            None,
        )

    strongest_level = (
        "NOT_VERIFIED"
    )

    official_careers_found = False

    exact_job_verified = False

    careers_url = None

    verification_rank = {
        "NOT_VERIFIED": 0,
        "EXTERNAL_ONLY": 1,
        "CAREERS_CONFIRMED": 2,
        "EXACT_JOB_VERIFIED": 3,
    }

    for signal in company.signals:

        level = getattr(
            signal,
            "verification_level",
            "NOT_VERIFIED",
        )

        if (
            verification_rank.get(
                level,
                0,
            )
            >
            verification_rank.get(
                strongest_level,
                0,
            )
        ):
            strongest_level = level

        if getattr(
            signal,
            "official_careers_found",
            False,
        ):
            official_careers_found = True

        if getattr(
            signal,
            "exact_job_verified",
            False,
        ):
            exact_job_verified = True

        signal_careers_url = getattr(
            signal,
            "careers_url",
            None,
        )

        if signal_careers_url:
            careers_url = (
                signal_careers_url
            )

    return (
        strongest_level,
        official_careers_found,
        exact_job_verified,
        careers_url,
    )


def run_batch_sdr(
    query: str,
    count: int = 10,
    max_results: int | None = None,
) -> list[BatchLead]:
    """
    Discover, enrich, verify, score and prepare
    outreach intelligence for multiple prospects.
    """

    print()
    print("=" * 60)
    print("       ESSEMVEE BATCH SDR")
    print("=" * 60)

    print()

    print(
        f"[BATCH] Search query: {query}"
    )

    print(
        f"[BATCH] Discovery count: {count}"
    )

    # --------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------

    discovery = ProspectDiscovery()

    prospects = discovery.discover(
        query=query,
        count=count,
    )

    print()

    print(
        f"[BATCH] Qualified prospects discovered: "
        f"{len(prospects)}"
    )

    if not prospects:

        print(
            "[BATCH] No qualified prospects found."
        )

        return []

    leads: list[BatchLead] = []

    # --------------------------------------------------
    # PROCESS PROSPECTS
    # --------------------------------------------------

    for index, (
        candidate,
        discovered_signal,
    ) in enumerate(
        prospects,
        start=1,
    ):

        print()
        print("-" * 60)

        print(
            f"[BATCH] Processing "
            f"{index}/{len(prospects)}: "
            f"{candidate.company_name}"
        )

        print(
            f"[BATCH] Signal: "
            f"{discovered_signal.signal_type}"
        )

        try:

            (
                company,
                result,
                outreach,
            ) = analyze_candidate_with_outreach(
                candidate=candidate,
                signals=[
                    discovered_signal,
                ],
            )

            lead = BatchLead(
                candidate=candidate,
                company=company,
                result=result,
                outreach=outreach,
            )

            leads.append(
                lead
            )

            print()

            print(
                f"[BATCH] Completed: "
                f"{candidate.company_name}"
            )

            print(
                f"[BATCH] Opportunity: "
                f"{result.opportunity_score}/100"
            )

            print(
                f"[BATCH] Priority: "
                f"{result.priority}"
            )

            print(
                f"[BATCH] Service: "
                f"{result.recommended_service}"
            )

        except Exception as exc:

            print()

            print(
                f"[BATCH] ERROR processing "
                f"{candidate.company_name}: "
                f"{exc}"
            )

            continue

    # --------------------------------------------------
    # RANK
    # --------------------------------------------------

    leads.sort(
        key=_sort_key
    )

    # --------------------------------------------------
    # OPTIONAL LIMIT
    # --------------------------------------------------

    if max_results is not None:

        if max_results < 0:

            raise ValueError(
                "max_results cannot be negative."
            )

        leads = leads[
            :max_results
        ]

    print()
    print("=" * 60)

    print(
        f"[BATCH] Final leads: "
        f"{len(leads)}"
    )

    print("=" * 60)

    return leads


def print_batch_results(
    leads: list[BatchLead],
) -> None:
    """
    Print a production-style ranked batch report.
    """

    print()
    print("=" * 60)
    print("       ESSEMVEE BATCH RESULTS")
    print("=" * 60)

    if not leads:

        print()
        print(
            "No batch leads available."
        )

        print(
            "=" * 60
        )

        return

    for index, lead in enumerate(
        leads,
        start=1,
    ):

        result = lead.result

        (
            verification_level,
            official_careers_found,
            exact_job_verified,
            careers_url,
        ) = _get_verification_details(
            lead.company
        )

        print()
        print(
            f"#{index} "
            f"{lead.company.company_name}"
        )

        print(
            "-" * 40
        )

        # ---------------------------------------------
        # SCORE
        # ---------------------------------------------

        print(
            f"Priority:           "
            f"{result.priority}"
        )

        print(
            f"Opportunity:        "
            f"{result.opportunity_score}/100"
        )

        print(
            f"ICP Fit:            "
            f"{result.icp_score}/100"
        )

        print(
            f"Intent:             "
            f"{result.intent_score}/100"
        )

        print(
            f"Evidence Quality:   "
            f"{result.evidence_quality}/100"
        )

        # ---------------------------------------------
        # SERVICE
        # ---------------------------------------------

        print(
            f"Service:            "
            f"{result.recommended_service}"
        )

        # ---------------------------------------------
        # VERIFICATION
        # ---------------------------------------------

        print()

        print(
            f"Verification:       "
            f"{verification_level}"
        )

        print(
            f"Official Careers:   "
            f"{'YES' if official_careers_found else 'NO'}"
        )

        print(
            f"Exact Job:          "
            f"{'YES' if exact_job_verified else 'NO'}"
        )

        if careers_url:

            print(
                f"Careers URL:        "
                f"{careers_url}"
            )

        # ---------------------------------------------
        # COMPANY
        # ---------------------------------------------

        print()

        print(
            f"Company:            "
            f"{lead.company.company_name}"
        )

        print(
            f"Website:            "
            f"{lead.company.website}"
        )

        print(
            f"Country:            "
            f"{lead.company.country}"
        )

        print(
            f"Industry:           "
            f"{lead.company.industry}"
        )

        # ---------------------------------------------
        # TRIGGER
        # ---------------------------------------------

        print()

        if lead.outreach.trigger:

            print(
                "Trigger:"
            )

            print(
                f"  {lead.outreach.trigger}"
            )

        # ---------------------------------------------
        # ACTION
        # ---------------------------------------------

        print()

        print(
            "Recommended Action:"
        )

        print(
            f"  {result.recommended_action}"
        )

    print()
    print("=" * 60)