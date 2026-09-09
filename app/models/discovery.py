from pydantic import BaseModel, Field


class DiscoveryCandidate(BaseModel):
    company_name: str

    website: str | None = None

    country: str | None = None

    industry: str | None = None

    employee_count: int | None = None

    description: str | None = None

    discovery_source: str

    source_url: str | None = None

    confidence: int = Field(
        default=50,
        ge=0,
        le=100,
    )


class DiscoveryResult(BaseModel):
    candidates: list[DiscoveryCandidate] = Field(
        default_factory=list
    )