from app.services.company_enrichment import (
    enrich_candidate,
)

from app.models.discovery import (
    DiscoveryCandidate,
)


def main():

    candidate = DiscoveryCandidate(
        company_name="Deciphex",
        website="https://deciphex.com",
        country="Ireland",
        discovery_source="Brave Search",
        source_url=(
            "https://jobgether.com/"
            "offer/69a0d7b17f0cfae7f11efa47-"
            "senior-devops-engineer-"
            "ireland-based"
        ),
        confidence=80,
    )

    print()
    print("=" * 50)
    print("ESSEMVEE COMPANY ENRICHMENT")
    print("=" * 50)

    enriched = enrich_candidate(
        candidate
    )

    print()
    print(
        f"Company: "
        f"{enriched.company_name}"
    )

    print(
        f"Website: "
        f"{enriched.website}"
    )

    print(
        f"Country: "
        f"{enriched.country}"
    )

    print(
        f"Industry: "
        f"{enriched.industry}"
    )

    print(
        f"Employees: "
        f"{enriched.employee_count}"
    )

    print(
        f"Description: "
        f"{enriched.description}"
    )

    print(
        f"Confidence: "
        f"{enriched.confidence}/100"
    )

    print(
        f"Evidence URL: "
        f"{enriched.source_url}"
    )


if __name__ == "__main__":
    main()