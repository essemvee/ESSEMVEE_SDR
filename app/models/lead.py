from typing import Literal

from pydantic import BaseModel, Field


ServiceType = Literal[
    "Cloud Engineering",
    "DevOps",
    "DevSecOps",
    "AI & MLOps",
    "Data & Analytics",
]


Priority = Literal[
    "HOT",
    "WARM",
    "WATCH",
    "IGNORE",
]


VerificationLevel = Literal[
    "EXACT_JOB_VERIFIED",
    "CAREERS_CONFIRMED",
    "EXTERNAL_ONLY",
    "NOT_VERIFIED",
]


class CompanySignal(BaseModel):

    # -----------------------------------------
    # Signal
    # -----------------------------------------

    signal_type: str

    description: str

    # -----------------------------------------
    # Discovery
    # -----------------------------------------

    discovery_source: str | None = None

    # Actual source containing the evidence.
    source: str | None = None

    # Actual evidence URL.
    source_url: str | None = None

    # -----------------------------------------
    # Source quality
    # -----------------------------------------

    source_trust: int = Field(
        default=40,
        ge=0,
        le=100,
    )

    # -----------------------------------------
    # Signal strength
    # -----------------------------------------

    strength: int = Field(
        default=50,
        ge=0,
        le=100,
    )

    # -----------------------------------------
    # Evidence verification
    # -----------------------------------------

    # Whether the signal was independently
    # confirmed by the official company website.
    #
    # Kept for backward compatibility with
    # the existing scoring system.
    officially_verified: bool = False

    # More precise verification state.
    verification_level: VerificationLevel = (
        "NOT_VERIFIED"
    )

    # Whether the official careers page
    # was independently confirmed.
    official_careers_found: bool = False

    # Whether the exact advertised job
    # was independently confirmed.
    exact_job_verified: bool = False

    # Official careers page URL when found.
    careers_url: str | None = None


class CompanyInput(BaseModel):

    company_name: str

    website: str | None = None

    country: str | None = None

    industry: str | None = None

    employee_count: int | None = None

    description: str | None = None

    signals: list[CompanySignal] = Field(
        default_factory=list
    )


class ScoutResult(BaseModel):

    company_name: str

    # -----------------------------------------
    # Scoring
    # -----------------------------------------

    icp_score: int = Field(
        ge=0,
        le=100,
    )

    intent_score: int = Field(
        ge=0,
        le=100,
    )

    evidence_quality: int = Field(
        ge=0,
        le=100,
    )

    opportunity_score: int = Field(
        ge=0,
        le=100,
    )

    # -----------------------------------------
    # Classification
    # -----------------------------------------

    priority: Priority

    recommended_service: ServiceType

    # -----------------------------------------
    # Sales intelligence
    # -----------------------------------------

    likely_problem: str

    why_now: str

    decision_maker_role: str

    recommended_action: str

    reasoning: list[str]