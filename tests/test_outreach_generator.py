from app.models.outreach import (
    OutreachBrief,
)

from app.services.outreach_generator import (
    build_outreach_messages,
)


brief = OutreachBrief(
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
        (
            "Deciphex is building a global "
            "network of AI empowered "
            "pathologists."
        ),
    ],

    evidence_gaps=[
        (
            "Specific technical pain point is "
            "not established by the available "
            "evidence."
        ),
        (
            "Current cloud platform or technology "
            "stack is not established."
        ),
        (
            "Budget or procurement intent is "
            "not established."
        ),
        (
            "External consulting or delivery-partner "
            "intent is not established."
        ),
    ],

    decision_maker_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering hiring manager"
    ),

    essemvee_angle=(
        "Position ESSEMVEE as an Ireland-based "
        "DevOps delivery partner."
    ),

    recommended_action=(
        "Verify whether the Senior DevOps "
        "Engineer role is still open and "
        "explore whether interim delivery "
        "support is required."
    ),

    outreach_strategy=(
        "Use the hiring signal as the reason "
        "for contact."
    ),
)


messages = build_outreach_messages(
    brief
)


print()
print("=" * 60)
print("       ESSEMVEE OUTREACH PACKAGE")
print("=" * 60)

print()
print(f"Company: {messages.company_name}")
print(f"Priority: {messages.priority}")
print(
    f"Service: "
    f"{messages.recommended_service}"
)
print(
    f"Evidence Level: "
    f"{messages.evidence_level}"
)

print()
print("--- PERSONALIZATION POINTS ---")

for item in messages.personalization_points:
    print(f"- {item}")

print()
print("--- LINKEDIN CONNECTION ---")
print(messages.linkedin_connection)

print()
print("--- LINKEDIN FOLLOW-UP ---")
print(messages.linkedin_follow_up)

print()
print("--- EMAIL SUBJECT OPTIONS ---")

for index, subject in enumerate(
    messages.cold_email_subjects,
    start=1,
):
    print(
        f"{index}. {subject}"
    )

print()
print("--- COLD EMAIL ---")
print(messages.cold_email)

print()
print("--- DISCOVERY QUESTION ---")
print(messages.discovery_question)

print()
print("--- CALL OPENER ---")
print(messages.call_opener)

print()
print("--- CTA ---")
print(messages.cta)

print()
print("--- DO NOT CLAIM ---")

for item in messages.do_not_claim:
    print(f"- {item}")

print()
print("=" * 60)