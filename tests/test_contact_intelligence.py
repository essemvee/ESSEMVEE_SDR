from app.models.contact import ContactEvidence
from app.services.contact_intelligence import (
    build_contact_intelligence,
    build_decision_maker,
    calculate_role_match,
    calculate_contact_confidence,
    determine_email_status,
    determine_linkedin_status,
)


print()
print("=" * 60)
print("       ESSEMVEE CONTACT INTELLIGENCE TEST")
print("=" * 60)


# --------------------------------------------------
# Role matching
# --------------------------------------------------

print()
print("--- ROLE MATCHING ---")

cto_match = calculate_role_match(
    actual_role="CTO",
    recommended_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),
)

vp_match = calculate_role_match(
    actual_role="VP Engineering",
    recommended_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),
)

manager_match = calculate_role_match(
    actual_role="Engineering Manager",
    recommended_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),
)

print(
    f"CTO match: "
    f"{cto_match}/100"
)

print(
    f"VP Engineering match: "
    f"{vp_match}/100"
)

print(
    f"Engineering Manager match: "
    f"{manager_match}/100"
)


# --------------------------------------------------
# Contact status
# --------------------------------------------------

print()
print("--- CONTACT STATUS ---")

print(
    "LinkedIn missing:",
    determine_linkedin_status(
        None
    ),
)

print(
    "LinkedIn likely:",
    determine_linkedin_status(
        "https://www.linkedin.com/in/example-person"
    ),
)

print(
    "LinkedIn verified:",
    determine_linkedin_status(
        "https://www.linkedin.com/in/example-person",
        verified=True,
    ),
)

print(
    "Email missing:",
    determine_email_status(
        None
    ),
)

print(
    "Email unverified:",
    determine_email_status(
        "example@deciphex.com"
    ),
)

print(
    "Email verified:",
    determine_email_status(
        "example@deciphex.com",
        verified=True,
    ),
)


# --------------------------------------------------
# Build contacts
# --------------------------------------------------

print()
print("--- BUILDING CONTACTS ---")


cto = build_decision_maker(
    company_name="Deciphex",

    name="Example CTO",

    role="CTO",

    recommended_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),

    linkedin_url=(
        "https://www.linkedin.com/in/example-cto"
    ),

    linkedin_verified=True,

    email="cto@deciphex.com",

    email_verified=True,

    evidence=[
        ContactEvidence(
            source="Company website",

            source_url=(
                "https://deciphex.com"
            ),

            evidence_type=(
                "Leadership evidence"
            ),

            description=(
                "Test evidence showing "
                "an engineering leadership "
                "contact."
            ),

            confidence=95,
        ),

        ContactEvidence(
            source="LinkedIn",

            source_url=(
                "https://www.linkedin.com/"
                "in/example-cto"
            ),

            evidence_type=(
                "Professional profile"
            ),

            description=(
                "Test LinkedIn evidence."
            ),

            confidence=95,
        ),
    ],

    source_urls=[
        "https://deciphex.com",
        (
            "https://www.linkedin.com/"
            "in/example-cto"
        ),
    ],

    notes=[
        "Test contact only."
    ],
)


vp = build_decision_maker(
    company_name="Deciphex",

    name="Example VP",

    role="VP Engineering",

    recommended_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),

    linkedin_url=(
        "https://www.linkedin.com/in/example-vp"
    ),

    linkedin_verified=True,

    email=None,

    email_verified=False,

    evidence=[
        ContactEvidence(
            source="LinkedIn",

            source_url=(
                "https://www.linkedin.com/"
                "in/example-vp"
            ),

            evidence_type=(
                "Professional profile"
            ),

            description=(
                "Test LinkedIn evidence."
            ),

            confidence=90,
        ),
    ],

    source_urls=[
        (
            "https://www.linkedin.com/"
            "in/example-vp"
        ),
    ],

    notes=[
        "Test contact only.",
        "Business email not established.",
    ],
)


manager = build_decision_maker(
    company_name="Deciphex",

    name="Example Manager",

    role="Engineering Manager",

    recommended_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),

    linkedin_url=None,

    email=None,

    evidence=[
        ContactEvidence(
            source="Company website",

            source_url=(
                "https://deciphex.com"
            ),

            evidence_type=(
                "Leadership evidence"
            ),

            description=(
                "Test engineering management "
                "evidence."
            ),

            confidence=80,
        ),
    ],

    source_urls=[
        "https://deciphex.com",
    ],

    notes=[
        "Test contact only."
    ],
)


# --------------------------------------------------
# Display contacts
# --------------------------------------------------

for contact in [
    cto,
    vp,
    manager,
]:

    print()

    print(
        f"Name: "
        f"{contact.name}"
    )

    print(
        f"Role: "
        f"{contact.role}"
    )

    print(
        f"Role Match: "
        f"{contact.role_match}/100"
    )

    print(
        f"LinkedIn: "
        f"{contact.linkedin_url}"
    )

    print(
        f"LinkedIn Status: "
        f"{contact.linkedin_status}"
    )

    print(
        f"Email: "
        f"{contact.email}"
    )

    print(
        f"Email Status: "
        f"{contact.email_status}"
    )

    print(
        f"Confidence: "
        f"{contact.contact_confidence}/100"
    )


# --------------------------------------------------
# Contact confidence sanity check
# --------------------------------------------------

print()
print("--- CONFIDENCE TEST ---")

confidence = calculate_contact_confidence(
    role_match=100,
    linkedin_status="VERIFIED",
    email_status="VERIFIED",
    evidence_count=2,
)

print(
    f"Fully supported CTO confidence: "
    f"{confidence}/100"
)


# --------------------------------------------------
# Build Contact Intelligence
# --------------------------------------------------

print()
print("--- CONTACT INTELLIGENCE ---")

intelligence = build_contact_intelligence(
    company_name="Deciphex",

    recommended_role=(
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),

    contacts=[
        manager,
        vp,
        cto,
    ],

    research_notes=[
        "This is a test dataset.",
        "Contacts are not real outreach targets.",
    ],
)


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

print(
    "Ranked Contacts:"
)

for index, contact in enumerate(
    intelligence.decision_makers,
    start=1,
):

    print(
        f"{index}. "
        f"{contact.name} — "
        f"{contact.role} — "
        f"{contact.contact_confidence}/100"
    )


print()

if intelligence.best_contact:

    print(
        "BEST CONTACT:"
    )

    print(
        f"Name: "
        f"{intelligence.best_contact.name}"
    )

    print(
        f"Role: "
        f"{intelligence.best_contact.role}"
    )

    print(
        f"Confidence: "
        f"{intelligence.best_contact.contact_confidence}/100"
    )

else:

    print(
        "BEST CONTACT: None"
    )


print()
print("=" * 60)