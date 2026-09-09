from app.models.lead import CompanySignal
from app.services.evidence import (
    calculate_evidence_quality,
)


signals = [
    CompanySignal(
        signal_type="Hiring",
        description=(
            "Company is hiring a Senior DevOps Engineer "
            "with Azure and Terraform experience."
        ),
        discovery_source="Brave Search",
        source="Jobgether",
        source_url=(
            "https://jobgether.com/offer/test"
        ),
        source_trust=70,
        strength=85,
        officially_verified=False,
    )
]


score = calculate_evidence_quality(
    signals
)


print(
    f"Evidence Quality: {score}/100"
)