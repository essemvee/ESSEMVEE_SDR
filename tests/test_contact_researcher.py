from app.services.contact_researcher import (
    research_contacts,
)


company = "Deciphex"

website = (
    "https://deciphex.com"
)


result = research_contacts(
    company_name=company,
    website=website,
)


print()
print("=" * 60)
print("       ESSEMVEE CONTACT RESEARCH")
print("=" * 60)

print()

print(
    f"Company: "
    f"{result.company_name}"
)

print(
    f"Recommended Role: "
    f"{result.recommended_role}"
)

print(
    f"Contact Status: "
    f"{result.contact_status}"
)

print()

print(
    "Decision Makers:"
)

for index, contact in enumerate(
    result.decision_makers,
    start=1,
):

    print()

    print(
        f"{index}. "
        f"{contact.name}"
    )

    print(
        f"   Role: "
        f"{contact.role}"
    )

    print(
        f"   Role Match: "
        f"{contact.role_match}/100"
    )

    print(
        f"   LinkedIn: "
        f"{contact.linkedin_url}"
    )

    print(
        f"   LinkedIn Status: "
        f"{contact.linkedin_status}"
    )

    print(
        f"   Email: "
        f"{contact.email}"
    )

    print(
        f"   Email Status: "
        f"{contact.email_status}"
    )

    print(
        f"   Confidence: "
        f"{contact.contact_confidence}/100"
    )

    print(
        "   Evidence:"
    )

    for evidence in (
        contact.evidence
    ):

        print(
            f"   - {evidence.source}: "
            f"{evidence.description}"
        )

print()

print(
    "BEST CONTACT:"
)

if result.best_contact:

    print(
        f"Name: "
        f"{result.best_contact.name}"
    )

    print(
        f"Role: "
        f"{result.best_contact.role}"
    )

    print(
        f"LinkedIn: "
        f"{result.best_contact.linkedin_url}"
    )

    print(
        f"Email: "
        f"{result.best_contact.email}"
    )

    print(
        f"Confidence: "
        f"{result.best_contact.contact_confidence}/100"
    )

else:

    print(
        "No suitable contact discovered."
    )

print()

print(
    "Research Notes:"
)

for note in result.research_notes:

    print(
        f"- {note}"
    )

print()
print("=" * 60)