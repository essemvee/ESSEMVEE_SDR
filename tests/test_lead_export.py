from pathlib import Path

from app.models.lead import (
    CompanyInput,
    CompanySignal,
)

from app.models.outreach import (
    OutreachBrief,
)

from app.models.outreach_message import (
    OutreachMessageSet,
)

from app.services.lead_export import (
    build_lead_record,
    export_csv,
    export_excel,
)


company = CompanyInput(
    company_name="Deciphex",

    website="https://deciphex.com",

    country="Ireland",

    industry="healthtech",

    employee_count=None,

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


class MockResult:

    priority = "WARM"

    opportunity_score = 68

    icp_score = 55

    intent_score = 76

    evidence_quality = 76

    recommended_service = "DevOps"


outreach = OutreachBrief(

    company_name="Deciphex",

    priority="WARM",

    recommended_service="DevOps",

    trigger=(
        "Deciphex is hiring a remote "
        "Senior DevOps Engineer "
        "(Ireland based)."
    ),

    trigger_evidence=[
        "External source: Jobgether",

        (
            "Evidence URL: "
            "https://jobgether.com/offer/"
            "69a0d7b17f0cfae7f11efa47-"
            "senior-devops-engineer-"
            "ireland-based"
        ),

        (
            "Official company careers page "
            "was confirmed, but the exact job "
            "was not exposed in retrieved "
            "static HTML."
        ),
    ],

    what_we_know=[
        "Company: Deciphex",
        "Market: Ireland",
        "Industry: healthtech",
    ],

    evidence_gaps=[
        (
            "Specific technical pain point "
            "is not established."
        ),
        (
            "Current cloud platform or "
            "technology stack is not established."
        ),
        (
            "Budget or procurement intent "
            "is not established."
        ),
    ],

    decision_maker_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),

    essemvee_angle=(
        "Position ESSEMVEE as an Ireland-based "
        "DevOps delivery partner."
    ),

    recommended_action=(
        "Verify the Senior DevOps Engineer "
        "vacancy and explore whether "
        "additional delivery support is required."
    ),

    outreach_strategy=(
        "Use the hiring signal as the reason "
        "for contact."
    ),
)


messages = OutreachMessageSet(

    company_name="Deciphex",

    priority="WARM",

    recommended_service="DevOps",

    evidence_level="CAREERS_CONFIRMED",

    linkedin_connection=(
        "Hi, I work with ESSEMVEE."
    ),

    linkedin_follow_up=(
        "Thanks for connecting."
    ),

    cold_email_subjects=[
        "DevOps support for Deciphex",
        "DevOps capacity at Deciphex",
        "Additional DevOps engineering capacity",
    ],

    cold_email=(
        "Hi {First Name},\n\n"
        "I came across a report regarding "
        "a Senior DevOps Engineer opportunity "
        "at Deciphex in Ireland."
    ),

    discovery_question=(
        "Would additional external engineering "
        "capacity be useful while the position "
        "is being filled?"
    ),

    call_opener=(
        "Hi, this is Mohammed from ESSEMVEE."
    ),

    cta=(
        "Would you be open to a short "
        "15-minute conversation?"
    ),

    personalization_points=[
        "Market: Ireland",
        "Industry: healthtech",
        (
            "Deciphex is building a global "
            "network of AI empowered pathologists."
        ),
    ],

    do_not_claim=[
        (
            "Specific technical pain point "
            "is not established."
        ),
        (
            "Current cloud platform or "
            "technology stack is not established."
        ),
        (
            "Budget or procurement intent "
            "is not established."
        ),
        (
            "Exact vacancy is not officially "
            "verified."
        ),
    ],
)


result = MockResult()


record = build_lead_record(
    company=company,
    result=result,
    outreach=outreach,
    messages=messages,
)


output_dir = Path(
    "output"
)

output_dir.mkdir(
    exist_ok=True
)


csv_path = export_csv(
    [record],
    output_dir / "essemvee_leads.csv",
)


excel_path = export_excel(
    [record],
    output_dir / "essemvee_leads.xlsx",
)


print()
print("=" * 60)
print("       ESSEMVEE LEAD EXPORT TEST")
print("=" * 60)

print()

print(
    f"Company: "
    f"{record['Company']}"
)

print(
    f"Priority: "
    f"{record['Priority']}"
)

print(
    f"Opportunity: "
    f"{record['Opportunity Score']}/100"
)

print(
    f"Verification: "
    f"{record['Verification Level']}"
)

print(
    f"Official Careers: "
    f"{record['Official Careers Found']}"
)

print(
    f"Exact Job: "
    f"{record['Exact Job Verified']}"
)

print()

print(
    f"CSV: "
    f"{csv_path}"
)

print(
    f"Excel: "
    f"{excel_path}"
)

print()

print(
    f"Columns exported: "
    f"{len(record)}"
)

print()

print("=" * 60)