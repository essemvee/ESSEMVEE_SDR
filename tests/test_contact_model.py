from app.models.contact import (
    ContactEvidence,
    ContactIntelligence,
    DecisionMaker,
)


contact = DecisionMaker(
    company_name="Deciphex",

    name="Example Person",

    role="VP Engineering",

    role_match=95,

    linkedin_url=(
        "https://www.linkedin.com/in/example-person"
    ),

    linkedin_status="LIKELY",

    email="example@deciphex.com",

    email_status="UNVERIFIED",

    contact_confidence=78,

    evidence=[
        ContactEvidence(
            source="Company website",
            source_url="https://deciphex.com",
            evidence_type="Company leadership",

            description=(
                "Public company evidence associated "
                "the person with an engineering leadership role."
            ),

            confidence=85,
        )
    ],

    source_urls=[
        "https://deciphex.com",
    ],

    notes=[
        "Contact requires independent verification "
        "before outreach."
    ],
)


intelligence = ContactIntelligence(
    company_name="Deciphex",

    recommended_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),

    decision_makers=[
        contact,
    ],

    contact_status="PARTIAL",

    best_contact=contact,

    research_notes=[
        "Example test contact only.",
        "Do not use this person for real outreach.",
    ],
)


print()
print("=" * 60)
print("       ESSEMVEE CONTACT MODEL TEST")
print("=" * 60)

print()

print(
    f"Company: "
    f"{intelligence.company_name}"
)

print(
    f"Recommended Role: "
    f"{intelligence.recommended_role}"
)

print(
    f"Contact Status: "
    f"{intelligence.contact_status}"
)

print()

for person in intelligence.decision_makers:

    print(
        f"Name: "
        f"{person.name}"
    )

    print(
        f"Role: "
        f"{person.role}"
    )

    print(
        f"Role Match: "
        f"{person.role_match}/100"
    )

    print(
        f"LinkedIn: "
        f"{person.linkedin_url}"
    )

    print(
        f"LinkedIn Status: "
        f"{person.linkedin_status}"
    )

    print(
        f"Email: "
        f"{person.email}"
    )

    print(
        f"Email Status: "
        f"{person.email_status}"
    )

    print(
        f"Confidence: "
        f"{person.contact_confidence}/100"
    )

print()

print("=" * 60)