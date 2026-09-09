from app.models.discovery import (
    DiscoveryCandidate,
)

from app.services.discovery import (
    normalize_candidates,
)


candidates = [
    DiscoveryCandidate(
        company_name=" Example SaaS ",
        website=" https://example.com ",
        country=" Ireland ",
        industry=" B2B SaaS ",
        employee_count=120,
        description=(
            "Growing B2B SaaS company."
        ),
        discovery_source="manual",
        source_url="https://example.com",
        confidence=90,
    ),
    DiscoveryCandidate(
        company_name="Example SaaS",
        website="https://example.com",
        country="Ireland",
        industry="B2B SaaS",
        employee_count=120,
        discovery_source="manual",
        confidence=80,
    ),
]


result = normalize_candidates(
    candidates
)


print()
print("==============================")
print("ESSEMVEE DISCOVERY")
print("==============================")
print()
print(
    f"Candidates found: "
    f"{len(candidates)}"
)
print(
    f"Unique candidates: "
    f"{len(result.candidates)}"
)

for candidate in result.candidates:

    print()
    print(
        f"Company: "
        f"{candidate.company_name}"
    )

    print(
        f"Website: "
        f"{candidate.website}"
    )

    print(
        f"Country: "
        f"{candidate.country}"
    )

    print(
        f"Industry: "
        f"{candidate.industry}"
    )