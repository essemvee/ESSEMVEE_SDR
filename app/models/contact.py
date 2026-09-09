from typing import Literal

from pydantic import BaseModel, Field


ContactStatus = Literal[
    "VERIFIED",
    "LIKELY",
    "UNVERIFIED",
    "NOT_FOUND",
]


class ContactEvidence(BaseModel):
    """
    Evidence supporting a decision-maker contact.
    """

    source: str

    source_url: str | None = None

    evidence_type: str

    description: str

    confidence: int = Field(
        ge=0,
        le=100,
    )


class DecisionMaker(BaseModel):
    """
    Decision-maker identified for an ESSEMVEE prospect.

    Contact information must be evidence-based.
    The system must not invent names, emails,
    LinkedIn URLs, or job titles.
    """

    company_name: str

    name: str | None = None

    role: str

    role_match: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    linkedin_url: str | None = None

    linkedin_status: ContactStatus = (
        "NOT_FOUND"
    )

    email: str | None = None

    email_status: ContactStatus = (
        "NOT_FOUND"
    )

    contact_confidence: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    evidence: list[ContactEvidence] = []

    source_urls: list[str] = []

    notes: list[str] = []


class ContactIntelligence(BaseModel):
    """
    Contact intelligence generated for a qualified
    company opportunity.

    Multiple decision makers may be returned because
    the first person may not always be reachable
    or appropriate.
    """

    company_name: str

    recommended_role: str

    decision_makers: list[DecisionMaker] = []

    contact_status: Literal[
        "FOUND",
        "PARTIAL",
        "NOT_FOUND",
    ] = "NOT_FOUND"

    best_contact: DecisionMaker | None = None

    research_notes: list[str] = []