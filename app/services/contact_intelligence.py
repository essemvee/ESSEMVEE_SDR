from app.models.contact import (
    ContactIntelligence,
    DecisionMaker,
)

from app.services.contact_verifier import (
    select_best_contact,
    verify_contact,
)


# ============================================================
# BUILD CONTACT INTELLIGENCE
# ============================================================

def build_contact_intelligence(
    company_name: str,
    recommended_role: str,
    contacts: list[DecisionMaker],
) -> ContactIntelligence:

    verified_contacts = []

    for contact in contacts:

        verified = verify_contact(
            contact
        )

        verified_contacts.append(
            verified
        )

    # --------------------------------------------------------
    # Highest confidence first.
    # --------------------------------------------------------

    verified_contacts.sort(
        key=lambda contact: (
            contact.contact_confidence,
            contact.role_match,
            bool(contact.linkedin_url),
            bool(contact.email),
        ),
        reverse=True,
    )

    best_contact = select_best_contact(
        verified_contacts
    )

    # --------------------------------------------------------
    # Contact status
    # --------------------------------------------------------

    if not verified_contacts:

        contact_status = "NOT_FOUND"

    elif best_contact:

        has_linkedin = any(
            contact.linkedin_url
            for contact in verified_contacts
        )

        has_email = any(
            contact.email
            for contact in verified_contacts
        )

        if (
            has_linkedin
            and has_email
        ):

            contact_status = "FOUND"

        else:

            contact_status = "PARTIAL"

    else:

        contact_status = "NOT_FOUND"

    # --------------------------------------------------------
    # Research notes
    # --------------------------------------------------------

    research_notes = []

    if not verified_contacts:

        research_notes.append(
            "No decision-maker contacts were discovered."
        )

    else:

        research_notes.append(
            f"{len(verified_contacts)} "
            "decision-maker candidate(s) discovered."
        )

    if best_contact:

        research_notes.append(
            (
                f"Best supported contact is "
                f"{best_contact.name} "
                f"({best_contact.role})."
            )
        )

        if not best_contact.email:

            research_notes.append(
                "No verified email was discovered."
            )

        if not best_contact.linkedin_url:

            research_notes.append(
                "No LinkedIn profile was discovered."
            )

    else:

        research_notes.append(
            (
                "No contact met the minimum "
                "confidence threshold."
            )
        )

    return ContactIntelligence(
        company_name=company_name,
        recommended_role=recommended_role,
        decision_makers=verified_contacts,
        contact_status=contact_status,
        best_contact=best_contact,
        research_notes=research_notes,
    )