from pydantic import BaseModel, Field


class Signal(BaseModel):

    signal_type: str

    title: str

    description: str

    # How we discovered the evidence.
    discovery_source: str | None = None

    # The actual source containing the evidence.
    source: str | None = None

    # Actual evidence URL.
    source_url: str | None = None

    # Trustworthiness of the evidence source.
    source_trust: int = Field(
        default=40,
        ge=0,
        le=100,
    )

    # Strength of the actual signal.
    strength: int = Field(
        default=50,
        ge=0,
        le=100,
    )

    # Whether the signal was independently
    # confirmed by the official company website.
    officially_verified: bool = False