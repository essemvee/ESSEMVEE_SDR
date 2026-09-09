from app.models.discovery import (
    DiscoveryCandidate,
    DiscoveryResult,
)


def normalize_candidate(
    candidate: DiscoveryCandidate,
) -> DiscoveryCandidate:

    candidate.company_name = (
        candidate.company_name.strip()
    )

    if candidate.country:
        candidate.country = (
            candidate.country.strip()
        )

    if candidate.industry:
        candidate.industry = (
            candidate.industry.strip()
        )

    if candidate.website:
        candidate.website = (
            candidate.website.strip()
        )

    return candidate


def normalize_candidates(
    candidates: list[DiscoveryCandidate],
) -> DiscoveryResult:

    normalized = []

    seen = set()

    for candidate in candidates:

        candidate = normalize_candidate(
            candidate
        )

        key = candidate.company_name.lower()

        if key in seen:
            continue

        seen.add(key)

        normalized.append(candidate)

    return DiscoveryResult(
        candidates=normalized
    )