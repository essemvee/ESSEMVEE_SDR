from app.models.lead import (
    CompanyInput,
    CompanySignal,
    ScoutResult,
)

from app.services.outreach import (
    build_outreach_brief,
)


company = CompanyInput(
    company_name="Deciphex",

    website="https://deciphex.com",

    country="Ireland",

    industry="healthtech",

    description=(
        "Deciphex is building a global network "
        "of AI empowered pathologists."
    ),

    signals=[
        CompanySignal(
            signal_type="Hiring",

            description=(
                "Deciphex is hiring a remote "
                "Senior DevOps Engineer "
                "(Ireland based)."
            ),

            discovery_source="Brave Search",

            source="Jobgether",

            source_url=(
                "https://jobgether.com/offer/"
                "69a0d7b17f0cfae7f11efa47-"
                "senior-devops-engineer-"
                "ireland-based"
            ),

            source_trust=70,

            strength=65,

            officially_verified=False,

            verification_level=(
                "CAREERS_CONFIRMED"
            ),

            official_careers_found=True,

            exact_job_verified=False,

            careers_url=(
                "https://www.deciphex.com/"
                "careers/open-roles"
            ),
        )
    ],
)


result = ScoutResult(
    company_name="Deciphex",

    icp_score=55,

    intent_score=78,

    evidence_quality=76,

    opportunity_score=68,

    priority="WARM",

    recommended_service="DevOps",

    likely_problem=(
        "Deciphex appears to have a current "
        "need for senior DevOps capability."
    ),

    why_now=(
        "A Senior DevOps Engineer vacancy "
        "is an active service-relevant signal."
    ),

    decision_maker_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering hiring manager"
    ),

    recommended_action=(
        "Verify whether the Senior DevOps "
        "Engineer role is still open and "
        "explore whether interim delivery "
        "support is required."
    ),

    reasoning=[
        "Deciphex operates in healthtech.",

        "A Senior DevOps Engineer hiring "
        "signal is relevant to ESSEMVEE.",

        "The exact vacancy is not independently "
        "verified on the official website.",
    ],
)


brief = build_outreach_brief(
    company=company,
    result=result,
)


print()
print("=" * 60)
print("       ESSEMVEE OUTREACH BRIEF")
print("=" * 60)

print()
print(
    f"Company: "
    f"{brief.company_name}"
)

print(
    f"Priority: "
    f"{brief.priority}"
)

print(
    f"Service: "
    f"{brief.recommended_service}"
)

print()
print(
    f"Trigger:\n"
    f"{brief.trigger}"
)

print()
print("Trigger Evidence:")

for item in brief.trigger_evidence:
    print(f"- {item}")

print()
print("What We Know:")

for item in brief.what_we_know:
    print(f"- {item}")

print()
print("Evidence Gaps:")

for item in brief.evidence_gaps:
    print(f"- {item}")

print()
print(
    f"Decision Maker:\n"
    f"{brief.decision_maker_role}"
)

print()
print(
    f"ESSEMVEE Angle:\n"
    f"{brief.essemvee_angle}"
)

print()
print(
    f"Recommended Action:\n"
    f"{brief.recommended_action}"
)

print()
print(
    f"Outreach Strategy:\n"
    f"{brief.outreach_strategy}"
)

print()
print("=" * 60)