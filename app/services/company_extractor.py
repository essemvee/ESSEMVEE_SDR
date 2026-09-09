import re
from urllib.parse import urlparse

from app.models.discovery import DiscoveryCandidate


def get_domain(url: str) -> str:
    parsed = urlparse(url)

    hostname = parsed.hostname

    if not hostname:
        return ""

    hostname = hostname.lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    return hostname


def company_from_domain(url: str) -> str:
    hostname = get_domain(url)

    if not hostname:
        return ""

    parts = hostname.split(".")

    if len(parts) < 2:
        return ""

    return parts[0].replace(
        "-",
        " ",
    ).title()


def extract_employer_from_title(
    title: str,
) -> str | None:

    if not title:
        return None

    title = title.strip()

    match = re.search(
        r"\bat\s+(.+?)$",
        title,
        flags=re.IGNORECASE,
    )

    if match:

        employer = (
            match.group(1)
            .strip()
            .rstrip("., ")
        )

        # Remove common trailing location text
        employer = re.sub(
            r"\s*\(.*?\)\s*$",
            "",
            employer,
        ).strip()

        if len(employer) >= 3:
            return employer

    # Example:
    # Senior DevOps Engineer - Beyond, Inc. | Built In
    match = re.search(
        r"\-\s+(.+?)(?:\s*\|\s*.*)?$",
        title,
    )

    if match:

        employer = (
            match.group(1)
            .strip()
            .rstrip("., ")
        )

        if len(employer) >= 3:
            return employer

    return None


def extract_employer_from_description(
    description: str,
) -> str | None:

    if not description:
        return None

    patterns = [
        r"^([A-Z][A-Za-z0-9&.,' -]{2,60}?)\s+is hiring",
        r"^([A-Z][A-Za-z0-9&.,' -]{2,60}?)\s+is looking for",
        r"^([A-Z][A-Za-z0-9&.,' -]{2,60}?)\s+is seeking",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            description.strip(),
        )

        if match:

            employer = (
                match.group(1)
                .strip()
                .rstrip("., ")
            )

            if len(employer) >= 3:
                return employer

    return None


def extract_company_from_result(
    result: dict,
    country: str = "Ireland",
) -> DiscoveryCandidate | None:

    url = result.get("url")

    if not url:
        return None

    title = result.get(
        "title",
        "",
    )

    description = result.get(
        "description",
        "",
    )

    # First trust the title.
    employer = extract_employer_from_title(
        title
    )

    # Then try the description.
    if not employer:

        employer = (
            extract_employer_from_description(
                description
            )
        )

    if employer:

        company_name = employer
        confidence = 80

    else:

        company_name = company_from_domain(
            url
        )

        confidence = 60

    if not company_name:
        return None

    domain = get_domain(url)

    return DiscoveryCandidate(
        company_name=company_name,
        website=f"https://{domain}",
        country=country,
        description=description,
        discovery_source="Brave Search",
        source_url=url,
        confidence=confidence,
    )