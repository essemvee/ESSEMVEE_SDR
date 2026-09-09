from app.models.outreach import OutreachBrief
from app.models.outreach_message import (
    OutreachMessageSet,
)


def _get_evidence_level(
    brief: OutreachBrief,
) -> str:
    """
    Determine the strongest evidence level available
    from the OutreachBrief.
    """

    evidence_text = " ".join(
        brief.trigger_evidence
    ).lower()

    if (
        "independently exposes the exact job"
        in evidence_text
        or "exact job verified"
        in evidence_text
        or "exact_job_verified"
        in evidence_text
    ):
        return "EXACT_JOB_VERIFIED"

    if (
        "official company careers page was confirmed"
        in evidence_text
        or "careers page was confirmed"
        in evidence_text
        or "careers_confirmed"
        in evidence_text
    ):
        return "CAREERS_CONFIRMED"

    if (
        "external source only"
        in evidence_text
        or "external_only"
        in evidence_text
    ):
        return "EXTERNAL_ONLY"

    return "NOT_VERIFIED"


def _build_trigger_statement(
    brief: OutreachBrief,
    evidence_level: str,
) -> str:
    """
    Build an evidence-safe statement describing
    the trigger.
    """

    trigger = brief.trigger.strip()

    if not trigger:
        return (
            "I noticed a recent development that "
            "may be relevant to your engineering team."
        )

    trigger = trigger.rstrip(". ")

    if evidence_level == "EXACT_JOB_VERIFIED":
        return (
            f"I noticed that {trigger.lower()}."
        )

    if evidence_level == "CAREERS_CONFIRMED":
        return (
            f"I came across a report that "
            f"{trigger.lower()}."
        )

    if evidence_level == "EXTERNAL_ONLY":
        return (
            f"I came across an external report that "
            f"{trigger.lower()}."
        )

    return (
        f"I came across information suggesting that "
        f"{trigger.lower()}."
    )


def _build_personalization_points(
    brief: OutreachBrief,
) -> list[str]:
    """
    Build safe personalization points directly
    from evidence contained in the brief.
    """

    points: list[str] = []

    for item in brief.what_we_know:

        item = item.strip()

        if not item:
            continue

        lowered = item.lower()

        if lowered.startswith("company:"):
            continue

        points.append(item)

        if len(points) >= 3:
            break

    return points


def _build_do_not_claim(
    brief: OutreachBrief,
) -> list[str]:
    """
    Convert evidence gaps into explicit safeguards.
    """

    claims: list[str] = []

    for gap in brief.evidence_gaps:

        gap = gap.strip()

        if gap:
            claims.append(gap)

    default_claims = [
        (
            "Do not claim the exact vacancy is officially "
            "verified unless the evidence level is "
            "EXACT_JOB_VERIFIED."
        ),
        (
            "Do not claim a specific cloud platform or "
            "technology stack unless established by evidence."
        ),
        (
            "Do not claim a specific technical pain point "
            "unless established by evidence."
        ),
        (
            "Do not claim that the company has approved "
            "an external consulting budget."
        ),
    ]

    existing = " ".join(
        claims
    ).lower()

    for claim in default_claims:

        if (
            "exact vacancy" in claim.lower()
            and "exact vacancy" in existing
        ):
            continue

        if (
            "cloud platform" in claim.lower()
            and "cloud platform" in existing
        ):
            continue

        if (
            "technical pain point" in claim.lower()
            and "technical pain point" in existing
        ):
            continue

        if (
            "external consulting" in claim.lower()
            and "external consulting" in existing
        ):
            continue

        claims.append(claim)

    return claims


def _build_cold_email_subjects(
    company: str,
    service: str,
) -> list[str]:
    """
    Generate concise subject-line options.
    """

    subjects = [
        f"{service} support for {company}",
    ]

    if service.lower() == "devops":
        subjects.append(
            f"DevOps capacity at {company}"
        )
    else:
        subjects.append(
            f"{service} delivery support at {company}"
        )

    subjects.append(
        f"Additional {service} engineering capacity"
    )

    return subjects


def build_outreach_messages(
    brief: OutreachBrief,
) -> OutreachMessageSet:
    """
    Generate evidence-safe outbound messages.

    This layer does not perform new research and
    does not invent company facts.
    """

    evidence_level = _get_evidence_level(
        brief
    )

    trigger_statement = _build_trigger_statement(
        brief,
        evidence_level,
    )

    service = (
        brief.recommended_service.strip()
    )

    company = (
        brief.company_name.strip()
    )

    personalization_points = (
        _build_personalization_points(
            brief
        )
    )

    do_not_claim = _build_do_not_claim(
        brief
    )

    # --------------------------------------------------
    # LinkedIn connection
    # --------------------------------------------------

    linkedin_connection = (
        f"Hi, I work with ESSEMVEE, an "
        f"Ireland-based technology consulting "
        f"team focused on {service}. "
        f"{trigger_statement} "
        f"I'd be interested in connecting."
    )

    # --------------------------------------------------
    # LinkedIn follow-up
    # --------------------------------------------------

    linkedin_follow_up = (
        f"Thanks for connecting. "
        f"{trigger_statement} "
        f"We help technology teams add flexible "
        f"{service} delivery capacity when they "
        f"need additional engineering support. "
        f"Would it be useful to have a brief "
        f"conversation about the role's scope "
        f"and whether additional delivery capacity "
        f"could help while the team is hiring?"
    )

    # --------------------------------------------------
    # Cold email subjects
    # --------------------------------------------------

    cold_email_subjects = (
        _build_cold_email_subjects(
            company=company,
            service=service,
        )
    )

    # --------------------------------------------------
    # Cold email
    # --------------------------------------------------

    cold_email = (
        f"Hi {{First Name}},\n\n"
        f"{trigger_statement} "
        f"We work with technology teams through "
        f"ESSEMVEE, an Ireland-based technology "
        f"consulting company providing {service} "
        f"engineering capability.\n\n"
        f"If the team is looking for additional "
        f"capacity while building out its internal "
        f"capability, we may be able to help with "
        f"flexible delivery support.\n\n"
        f"I don't want to assume the scope or "
        f"technical requirements behind the role, "
        f"so I wanted to ask: would a short "
        f"conversation about the team's current "
        f"priorities be useful?\n\n"
        f"Best,\n"
        f"Mohammed\n"
        f"ESSEMVEE Technology Services"
    )

    # --------------------------------------------------
    # Call opener
    # --------------------------------------------------

    call_opener = (
        f"Hi, this is Mohammed from ESSEMVEE. "
        f"{trigger_statement} "
        f"I wanted to quickly understand whether "
        f"you are purely looking to build the "
        f"internal team or whether additional "
        f"{service} delivery capacity could also "
        f"be useful."
    )

    # --------------------------------------------------
    # CTA
    # --------------------------------------------------

    cta = (
        "Would you be open to a short 15-minute "
        "conversation to understand the team's "
        "current priorities?"
    )

    # --------------------------------------------------
    # Discovery question
    # --------------------------------------------------

    discovery_question = (
        f"Is the {service} role primarily intended "
        f"to build internal capability, or would "
        f"additional external engineering capacity "
        f"also be useful while the position is "
        f"being filled?"
    )

    # --------------------------------------------------
    # Final structured result
    # --------------------------------------------------

    return OutreachMessageSet(
        company_name=company,
        priority=brief.priority,
        recommended_service=service,
        evidence_level=evidence_level,

        linkedin_connection=(
            linkedin_connection
        ),

        linkedin_follow_up=(
            linkedin_follow_up
        ),

        cold_email_subjects=(
            cold_email_subjects
        ),

        cold_email=(
            cold_email
        ),

        discovery_question=(
            discovery_question
        ),

        call_opener=(
            call_opener
        ),

        cta=(
            cta
        ),

        personalization_points=(
            personalization_points
        ),

        do_not_claim=(
            do_not_claim
        ),
    )