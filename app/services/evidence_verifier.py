import re
from urllib.parse import urlparse

import requests

from app.models.evidence import EvidenceVerification


# ============================================================
# URL NORMALIZATION
# ============================================================

def normalize_url(
    url: str,
) -> str:
    """
    Normalize normal URLs and Markdown-style URLs.

    Examples:

    https://deciphex.com
        ->
    https://deciphex.com

    [https://deciphex.com](https://deciphex.com)
        ->
    https://deciphex.com
    """

    if not url:
        return ""

    value = str(url).strip()

    # --------------------------------------------------------
    # Markdown link
    #
    # [label](https://example.com)
    #
    # Capture the URL inside (...)
    # --------------------------------------------------------

    markdown_match = re.search(
        r"\[[^\]]*\]\(\s*(https?://[^)\s]+)\s*\)",
        value,
        flags=re.IGNORECASE,
    )

    if markdown_match:

        return markdown_match.group(
            1
        ).strip()

    # --------------------------------------------------------
    # Normal HTTP / HTTPS URL
    # --------------------------------------------------------

    url_match = re.search(
        r"https?://[^\s\]\)]+",
        value,
        flags=re.IGNORECASE,
    )

    if url_match:

        return url_match.group(
            0
        ).strip()

    return value


# ============================================================
# ROOT URL
# ============================================================

def get_root_url(
    url: str,
) -> str:
    """
    Return only scheme + hostname.

    Example:

    https://deciphex.com/careers
        ->
    https://deciphex.com
    """

    normalized = normalize_url(
        url
    )

    if not normalized:
        return ""

    parsed = urlparse(
        normalized
    )

    if not parsed.hostname:
        return ""

    hostname = parsed.hostname.lower()

    if hostname.startswith(
        "www."
    ):
        hostname = hostname[4:]

    scheme = (
        parsed.scheme
        or "https"
    )

    return (
        f"{scheme}://{hostname}"
    )


# ============================================================
# COMPANY NAME NORMALIZATION
# ============================================================

def normalize_company_name(
    company_name: str,
) -> str:

    if not company_name:
        return ""

    value = company_name.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return value.strip()


def company_matches_text(
    company_name: str,
    text: str,
) -> bool:

    if not company_name or not text:
        return False

    company = normalize_company_name(
        company_name
    )

    normalized_text = normalize_company_name(
        text
    )

    return company in normalized_text


# ============================================================
# JOB TERMS
# ============================================================

def extract_job_terms(
    title: str,
) -> list[str]:

    text = (
        title or ""
    ).lower()

    terms = [
        "devops",
        "cloud",
        "azure",
        "aws",
        "kubernetes",
        "terraform",
        "platform engineering",
        "sre",
        "site reliability",
        "devsecops",
        "mlops",
        "machine learning",
        "data engineering",
    ]

    return [
        term
        for term in terms
        if term in text
    ]


# ============================================================
# PAGE FETCHING
# ============================================================

def fetch_page(
    url: str,
) -> tuple[str, str]:

    url = normalize_url(
        url
    )

    if not url:
        return "", ""

    try:

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/150.0 Safari/537.36"
                )
            },
            allow_redirects=True,
        )

        if response.status_code != 200:

            return "", url

        return (
            response.text,
            response.url,
        )

    except requests.RequestException:

        return "", url


# ============================================================
# HTML TO TEXT
# ============================================================

def html_to_text(
    html: str,
) -> str:

    if not html:
        return ""

    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        html,
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# CAREERS URLS
# ============================================================

def build_careers_urls(
    website: str,
) -> list[str]:

    root = get_root_url(
        website
    )

    if not root:
        return []

    return [
        f"{root}/careers",
        f"{root}/careers/",
        f"{root}/careers/home",
        f"{root}/careers/open-roles",
        f"{root}/jobs",
        f"{root}/jobs/",
        f"{root}/open-roles",
        f"{root}/openings",
    ]


# ============================================================
# CAREERS LANGUAGE
# ============================================================

def contains_careers_language(
    text: str,
) -> bool:

    if not text:
        return False

    text_lower = text.lower()

    phrases = [
        "open roles",
        "open positions",
        "job openings",
        "current openings",
        "join our team",
        "we are hiring",
        "we're hiring",
        "career opportunities",
        "vacancies",
        "apply now",
        "explore open roles",
        "explore open positions",
    ]

    return any(
        phrase in text_lower
        for phrase in phrases
    )


# ============================================================
# EXACT JOB MATCH
# ============================================================

def exact_job_matches(
    title: str,
    text: str,
) -> bool:

    if not title or not text:
        return False

    text_lower = text.lower()

    job_terms = extract_job_terms(
        title
    )

    if not job_terms:
        return False

    # --------------------------------------------------------
    # First check the complete job title.
    # --------------------------------------------------------

    normalized_title = re.sub(
        r"\s+",
        " ",
        title.lower(),
    ).strip()

    if normalized_title in text_lower:

        return True

    # --------------------------------------------------------
    # Then check strong combinations.
    # --------------------------------------------------------

    title_words = [
        word
        for word in re.findall(
            r"[a-z0-9]+",
            normalized_title,
        )
        if len(word) >= 3
    ]

    important_words = [
        word
        for word in title_words
        if word not in {
            "senior",
            "junior",
            "engineer",
            "remote",
            "based",
            "ireland",
        }
    ]

    if (
        len(important_words) >= 2
        and all(
            word in text_lower
            for word in important_words
        )
    ):

        return True

    return False


# ============================================================
# HIRING SIGNAL VERIFICATION
# ============================================================

def verify_hiring_signal(
    company_name: str,
    website: str,
    title: str,
    description: str,
) -> EvidenceVerification:
    """
    Verify a hiring signal against the
    company's official website.

    Important:

    The official careers page may exist without
    exposing individual jobs in static HTML.

    Therefore we distinguish:

    EXACT_JOB_VERIFIED
        Exact job evidence was found.

    CAREERS_CONFIRMED
        Official careers page was confirmed,
        but exact job evidence was not exposed.

    EXTERNAL_ONLY
        External hiring evidence exists, but
        official careers page could not be confirmed.

    NOT_VERIFIED
        No useful verification was found.
    """

    print(
        f"[DEBUG] Verifying hiring signal "
        f"for {company_name}"
    )

    normalized_website = get_root_url(
        website
    )

    print(
        f"[DEBUG] Normalized website: "
        f"{normalized_website}"
    )

    if not normalized_website:

        print(
            "[DEBUG] Invalid company website"
        )

        return EvidenceVerification(
            verification_level=(
                "NOT_VERIFIED"
            )
        )

    job_terms = extract_job_terms(
        title
    )

    print(
        f"[DEBUG] Job terms: "
        f"{job_terms}"
    )

    official_careers_found = False
    exact_job_verified = False
    careers_url = None

    # --------------------------------------------------------
    # Check official careers pages.
    # --------------------------------------------------------

    for candidate_url in build_careers_urls(
        normalized_website
    ):

        print(
            f"[DEBUG] Checking careers URL: "
            f"{candidate_url}"
        )

        html, final_url = fetch_page(
            candidate_url
        )

        if not html:

            print(
                f"[DEBUG] HTTP/Fetch failure: "
                f"{candidate_url}"
            )

            continue

        text = html_to_text(
            html
        )

        if not text:

            continue

        company_match = company_matches_text(
            company_name,
            text,
        )

        careers_language = (
            contains_careers_language(
                text
            )
        )

        print(
            f"[DEBUG] Company match: "
            f"{company_match}"
        )

        print(
            f"[DEBUG] Careers language: "
            f"{careers_language}"
        )

        # ----------------------------------------------------
        # Official careers page confirmed.
        # ----------------------------------------------------

        if (
            company_match
            and careers_language
        ):

            official_careers_found = True

            careers_url = (
                final_url
                or candidate_url
            )

            print(
                "[DEBUG] Official careers "
                f"page confirmed: {careers_url}"
            )

            # ------------------------------------------------
            # Look for the exact job.
            # ------------------------------------------------

            if exact_job_matches(
                title,
                text,
            ):

                exact_job_verified = True

                print(
                    "[DEBUG] Exact job match: True"
                )

                print(
                    "[DEBUG] EXACT_JOB_VERIFIED"
                )

                return EvidenceVerification(
                    official_careers_found=True,
                    exact_job_verified=True,
                    careers_url=careers_url,
                    verification_level=(
                        "EXACT_JOB_VERIFIED"
                    ),
                )

            print(
                "[DEBUG] Exact job match: False"
            )

            print(
                "[DEBUG] Official careers page "
                "found but exact job evidence "
                "was not exposed."
            )

    # --------------------------------------------------------
    # Official careers page exists, but the
    # individual job is not visible.
    # --------------------------------------------------------

    if official_careers_found:

        print(
            "[DEBUG] Official careers page confirmed."
        )

        print(
            "[DEBUG] Exact job not verified."
        )

        return EvidenceVerification(
            official_careers_found=True,
            exact_job_verified=False,
            careers_url=careers_url,
            verification_level=(
                "CAREERS_CONFIRMED"
            ),
        )

    # --------------------------------------------------------
    # No official careers page.
    #
    # The external source may still be valid,
    # but we cannot independently confirm it.
    # --------------------------------------------------------

    if title or description:

        print(
            "[DEBUG] Official careers page "
            "not confirmed."
        )

        print(
            "[DEBUG] Hiring evidence remains "
            "externally supported only."
        )

        return EvidenceVerification(
            official_careers_found=False,
            exact_job_verified=False,
            careers_url=None,
            verification_level=(
                "EXTERNAL_ONLY"
            ),
        )

    # --------------------------------------------------------
    # Nothing verified.
    # --------------------------------------------------------

    return EvidenceVerification(
        official_careers_found=False,
        exact_job_verified=False,
        careers_url=None,
        verification_level=(
            "NOT_VERIFIED"
        ),
    )