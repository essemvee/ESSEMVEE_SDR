from app.services.prospect_discovery import (
    ProspectDiscovery,
)

from app.services.pipeline import (
    analyze_candidate_with_outreach,
)


def main():

    print()
    print("=" * 60)
    print("       ESSEMVEE END-TO-END SDR TEST")
    print("=" * 60)

    query = (
        '"Senior DevOps Engineer" '
        '"Ireland" '
        '-LinkedIn '
        '-Indeed '
        '-Glassdoor '
        '-IrishJobs'
    )

    discovery = ProspectDiscovery()

    prospects = discovery.discover(
        query=query,
        count=5,
    )

    print()
    print(
        f"Discovered prospects: "
        f"{len(prospects)}"
    )

    if not prospects:

        print()
        print(
            "No qualified prospects found."
        )

        return

    for index, (
        candidate,
        discovered_signal,
    ) in enumerate(
        prospects,
        start=1,
    ):

        print()
        print("=" * 60)
        print(
            f"       PROSPECT {index}"
        )
        print("=" * 60)

        print(
            f"Company: "
            f"{candidate.company_name}"
        )

        print(
            f"Website: "
            f"{candidate.website}"
        )

        print(
            f"Country: "
            f"{candidate.country}"
        )

        print(
            f"Industry: "
            f"{candidate.industry}"
        )

        print(
            f"Employees: "
            f"{candidate.employee_count}"
        )

        print(
            f"Discovery Source: "
            f"{candidate.discovery_source}"
        )

        print(
            f"Evidence URL: "
            f"{candidate.source_url}"
        )

        print()
        print("--- SIGNAL ---")

        print(
            f"Type: "
            f"{discovered_signal.signal_type}"
        )

        print(
            f"Title: "
            f"{discovered_signal.title}"
        )

        print(
            f"Description: "
            f"{discovered_signal.description}"
        )

        print(
            f"Source: "
            f"{discovered_signal.source}"
        )

        print(
            f"Evidence URL: "
            f"{discovered_signal.source_url}"
        )

        print(
            f"Strength: "
            f"{discovered_signal.strength}/100"
        )

        # -----------------------------------------
        # Complete Scout + Outreach pipeline
        # -----------------------------------------

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

        # -----------------------------------------
        # Scoring
        # -----------------------------------------

        print()
        print("--- SCORING ---")

        print(
            f"ICP Score: "
            f"{result.icp_score}/100"
        )

        print(
            f"Intent Score: "
            f"{result.intent_score}/100"
        )

        print(
            f"Evidence Quality: "
            f"{result.evidence_quality}/100"
        )

        print(
            f"Opportunity Score: "
            f"{result.opportunity_score}/100"
        )

        print(
            f"Priority: "
            f"{result.priority}"
        )

        # -----------------------------------------
        # Sales Intelligence
        # -----------------------------------------

        print()
        print("--- SALES INTELLIGENCE ---")

        print(
            f"Recommended Service: "
            f"{result.recommended_service}"
        )

        print()
        print(
            f"Likely Problem:\n"
            f"{result.likely_problem}"
        )

        print()
        print(
            f"Why Now:\n"
            f"{result.why_now}"
        )

        print()
        print(
            f"Decision Maker:\n"
            f"{result.decision_maker_role}"
        )

        print()
        print(
            f"Recommended Action:\n"
            f"{result.recommended_action}"
        )

        print()
        print("Reasoning:")

        for reason in result.reasoning:

            print(
                f"- {reason}"
            )

        # -----------------------------------------
        # Outreach Brief
        # -----------------------------------------

        print()
        print("--- OUTREACH BRIEF ---")

        print(
            f"Company: "
            f"{outreach.company_name}"
        )

        print(
            f"Priority: "
            f"{outreach.priority}"
        )

        print(
            f"Recommended Service: "
            f"{outreach.recommended_service}"
        )

        print()
        print(
            f"Trigger:\n"
            f"{outreach.trigger}"
        )

        print()
        print("Trigger Evidence:")

        for evidence in (
            outreach.trigger_evidence
        ):

            print(
                f"- {evidence}"
            )

        print()
        print("What We Know:")

        for item in outreach.what_we_know:

            print(
                f"- {item}"
            )

        print()
        print("Evidence Gaps:")

        for gap in outreach.evidence_gaps:

            print(
                f"- {gap}"
            )

        print()
        print(
            f"Decision Maker:\n"
            f"{outreach.decision_maker_role}"
        )

        print()
        print(
            f"ESSEMVEE Angle:\n"
            f"{outreach.essemvee_angle}"
        )

        print()
        print(
            f"Recommended Action:\n"
            f"{outreach.recommended_action}"
        )

        print()
        print(
            f"Outreach Strategy:\n"
            f"{outreach.outreach_strategy}"
        )

        print()
        print("=" * 60)


if __name__ == "__main__":
    main()