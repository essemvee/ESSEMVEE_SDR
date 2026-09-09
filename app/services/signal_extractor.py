from app.models.signal import Signal


KEYWORD_STRENGTH = {
    "devops": 15,
    "azure": 10,
    "aws": 10,
    "kubernetes": 10,
    "terraform": 10,
    "platform engineering": 15,
    "mlops": 15,
    "devsecops": 15,
}


HIRING_PHRASES = [
    "we are hiring",
    "we're hiring",
    "is hiring",
    "are hiring",
    "currently hiring",
    "now hiring",
    "join our team",
    "job opening",
    "job openings",
    "open position",
    "open positions",
    "vacancy",
    "vacancies",
    "apply now",
    "apply for",
    "looking for a",
    "looking for an",
    "seeking a",
    "seeking an",
    "we are looking for",
    "we're looking for",
]


HIGH_TRUST_SOURCES = {
    "company careers page",
    "company website",
    "official company announcement",
    "official company blog",
    "official engineering blog",
}


MEDIUM_TRUST_SOURCES = {
    "linkedin",
    "industry publication",
    "technology publication",
    "conference",
    "executive interview",
}


def calculate_signal_strength(
    text: str,
) -> int:

    text = text.lower()

    score = 50

    for keyword, points in (
        KEYWORD_STRENGTH.items()
    ):

        if keyword in text:
            score += points

    return min(
        score,
        100,
    )


def determine_source_trust(
    source: str | None,
) -> int:

    normalized = (
        source or ""
    ).lower().strip()

    if normalized in HIGH_TRUST_SOURCES:
        return 100

    if normalized in MEDIUM_TRUST_SOURCES:
        return 70

    if normalized in {
        "jobgether",
        "builtin",
        "wellfound",
        "nijobs",
        "irishjobs",
    }:
        return 70

    if normalized:
        return 50

    return 40


def detect_signal_type(
    text: str,
) -> str:

    text = text.lower()

    if any(
        phrase in text
        for phrase in HIRING_PHRASES
    ):
        return "Hiring"

    if (
        "funding" in text
        or "raised" in text
        or "investment" in text
    ):
        return "Funding"

    if (
        "launched" in text
        or "launching" in text
        or "product launch" in text
    ):
        return "Product Launch"

    if (
        "security" in text
        or "devsecops" in text
        or "cybersecurity" in text
    ):
        return "Security"

    if (
        "cloud migration" in text
        or "migrating to azure" in text
        or "migrating to aws" in text
    ):
        return "Cloud"

    return "Other"


def extract_signal_from_result(
    company_name: str,
    result: dict,
    country: str = "Ireland",
) -> Signal | None:

    title = result.get(
        "title",
        "",
    )

    description = result.get(
        "description",
        "",
    )

    url = result.get(
        "url"
    )

    if not title and not description:
        return None

    combined_text = (
        f"{title} {description}"
    )

    signal_type = detect_signal_type(
        combined_text
    )

    strength = calculate_signal_strength(
        combined_text
    )

    # The result itself is the evidence source.
    #
    # Brave Search found the result, but
    # the actual page contains the evidence.

    discovery_source = (
        "Brave Search"
    )

    source = (
        "Unknown"
    )

    if url:

        url_lower = url.lower()

        if "jobgether.com" in url_lower:
            source = "Jobgether"

        elif "builtin.com" in url_lower:
            source = "Built In"

        elif "wellfound.com" in url_lower:
            source = "Wellfound"

        elif "nijobs.com" in url_lower:
            source = "NIJobs"

        elif "linkedin.com" in url_lower:
            source = "LinkedIn"

        elif "irishjobs.ie" in url_lower:
            source = "IrishJobs"

        else:
            source = "Web source"

    source_trust = (
        determine_source_trust(
            source
        )
    )

    return Signal(
        signal_type=signal_type,
        title=title,
        description=description,
        discovery_source=discovery_source,
        source=source,
        source_url=url,
        source_trust=source_trust,
        strength=strength,
        officially_verified=False,
    )