from typing import Literal

from pydantic import BaseModel


VerificationLevel = Literal[
    "EXACT_JOB_VERIFIED",
    "CAREERS_CONFIRMED",
    "EXTERNAL_ONLY",
    "NOT_VERIFIED",
]


class EvidenceVerification(BaseModel):

    official_careers_found: bool = False

    exact_job_verified: bool = False

    careers_url: str | None = None

    verification_level: VerificationLevel = (
        "NOT_VERIFIED"
    )