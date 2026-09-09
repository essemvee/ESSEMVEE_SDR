from app.models.lead import CompanyInput


TARGET_INDUSTRIES = {
    "saas",
    "software",
    "technology",
    "fintech",
    "healthtech",
    "ai",
    "artificial intelligence",
    "digital",
    "cybersecurity",
}


TARGET_MARKETS = {
    "ireland",
    "united kingdom",
    "uk",
    "england",
    "scotland",
    "wales",
    "northern ireland",
    "germany",
    "france",
    "netherlands",
    "spain",
    "italy",
    "sweden",
    "denmark",
    "norway",
    "finland",
    "belgium",
    "austria",
    "switzerland",
    "united states",
    "usa",
    "canada",
    "australia",
    "qatar",
    "saudi arabia",
    "united arab emirates",
    "uae",
}


RELEVANT_KEYWORDS = {
    "cloud",
    "azure",
    "aws",
    "kubernetes",
    "terraform",
    "devops",
    "devsecops",
    "platform engineering",
    "machine learning",
    "mlops",
    "artificial intelligence",
    "data engineering",
}


def calculate_icp_score(
    company: CompanyInput,
) -> int:
    """
    Calculate how closely a company matches
    ESSEMVEE's Ideal Customer Profile.

    Maximum score: 100
    """

    score = 0

    # -----------------------------------------
    # Company size — maximum 25
    # -----------------------------------------

    if company.employee_count is not None:

        employees = company.employee_count

        if 50 <= employees <= 300:
            score += 25

        elif 20 <= employees < 50:
            score += 20

        elif 301 <= employees <= 500:
            score += 20

        elif 10 <= employees < 20:
            score += 10

        elif 501 <= employees <= 1000:
            score += 10

    # -----------------------------------------
    # Industry — maximum 25
    # -----------------------------------------

    if company.industry:

        industry = (
            company.industry
            .lower()
            .strip()
        )

        if any(
            target in industry
            for target in TARGET_INDUSTRIES
        ):
            score += 25

    # -----------------------------------------
    # Market — maximum 15
    # -----------------------------------------

    if company.country:

        country = (
            company.country
            .lower()
            .strip()
        )

        if country in TARGET_MARKETS:
            score += 15

    # -----------------------------------------
    # Technology/service relevance
    # maximum 20
    # -----------------------------------------

    text_parts = [
        company.description,
        company.industry,
    ]

    # IMPORTANT:
    # Include actual buying signals.
    for signal in company.signals:

        text_parts.extend(
            [
                signal.signal_type,
                signal.description,
            ]
        )

    text = " ".join(
        filter(
            None,
            text_parts,
        )
    ).lower()

    technology_matches = sum(
        1
        for keyword in RELEVANT_KEYWORDS
        if keyword in text
    )

    score += min(
        technology_matches * 5,
        20,
    )

    # -----------------------------------------
    # Company information quality
    # maximum 10
    # -----------------------------------------

    if company.website:
        score += 5

    if company.description:
        score += 5

    return min(
        score,
        100,
    )