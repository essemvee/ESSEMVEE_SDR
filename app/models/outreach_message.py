from pydantic import BaseModel


class OutreachMessageSet(BaseModel):
    """
    Evidence-safe outbound sales package generated
    from an OutreachBrief.

    Messages must not introduce facts that are not
    supported by the underlying evidence.
    """

    company_name: str

    priority: str

    recommended_service: str

    evidence_level: str

    # --------------------------------------------------
    # LinkedIn
    # --------------------------------------------------

    linkedin_connection: str

    linkedin_follow_up: str

    # --------------------------------------------------
    # Email
    # --------------------------------------------------

    cold_email_subjects: list[str]

    cold_email: str

    # --------------------------------------------------
    # Sales conversation
    # --------------------------------------------------

    discovery_question: str

    call_opener: str

    cta: str

    # --------------------------------------------------
    # Personalization
    # --------------------------------------------------

    personalization_points: list[str]

    # --------------------------------------------------
    # Evidence safeguards
    # --------------------------------------------------

    do_not_claim: list[str]