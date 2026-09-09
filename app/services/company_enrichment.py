from __future__ import annotations

"""
======================================================================
ESSEMVEE AI SDR — COMPANY ENRICHMENT
======================================================================

Purpose
-------
Enrich a company discovered through:

    1. CRO / company registries
    2. Existing discovery
    3. Other future discovery sources

Important behaviour
-------------------
A company WITHOUT a known website is NOT automatically rejected.

For companies without a website:

    Company name
        ↓
    EmployerResolver
        ↓
    Strict official website verification
        ↓
    Official website OR None
        ↓
    Website enrichment
        ↓
    Industry / description / employee extraction

For brand-new companies, website absence is expected.

This module is READ-ONLY.

It:
    - searches public web information through EmployerResolver
    - reads public company websites
    - extracts company information

It does NOT:
    - send email
    - send LinkedIn messages
    - create campaigns
    - modify SDR records

Architecture note
-----------------
EmployerResolver is the SINGLE canonical website-resolution layer.

This module deliberately does NOT perform its own Brave website discovery.
That prevents conflicting website decisions and false positives from:

    - Companies House
    - CRO
    - directories
    - job boards
    - social media
    - commercial databases
    - news websites
======================================================================
"""

import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.models.discovery import DiscoveryCandidate
from app.services.employer_resolver import (
    EmployerResolver,
)
from app.services.web_discovery import WebDiscoverySource


# ======================================================================
# CONSTANTS
# ======================================================================

REQUEST_TIMEOUT = 20

MAX_PAGE_CHARS = 12000


# ======================================================================
# HTTP
# ======================================================================

def fetch_page(
    url: str,
) -> str | None:
    """
    Fetch a public webpage.

    Returns:
        HTML text
        or None if unavailable.
    """

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0 Safari/537.36"
                )
            },
            allow_redirects=True,
        )

        response.raise_for_status()

        content_type = (
            response.headers
            .get("Content-Type", "")
            .lower()
        )

        if (
            "text/html" not in content_type
            and "application/xhtml" not in content_type
        ):
            return None

        return response.text

    except Exception as exc:
        print(
            f"[ENRICH] Failed to fetch "
            f"{url}: {exc}"
        )

        return None


# ======================================================================
# URL HELPERS
# ======================================================================

def normalize_url(
    url: str | None,
) -> str | None:

    if not url:
        return None

    url = str(url).strip()

    if not url:
        return None

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    try:
        parsed = urlparse(url)

        if not parsed.netloc:
            return None

        return (
            f"{parsed.scheme}://"
            f"{parsed.netloc}"
        ).rstrip("/")

    except Exception:
        return None


def domain_from_url(
    url: str | None,
) -> str:

    if not url:
        return ""

    try:
        return (
            urlparse(url)
            .netloc
            .lower()
            .replace("www.", "")
        )

    except Exception:
        return ""


# ======================================================================
# TEXT
# ======================================================================

def html_to_text(
    html: str,
) -> str:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
        ]
    ):
        tag.decompose()

    text = soup.get_text(
        " ",
        strip=True,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text[:MAX_PAGE_CHARS]


# ======================================================================
# COMPANY NAME NORMALISATION
# ======================================================================

LEGAL_SUFFIXES = (
    " LIMITED",
    " LTD",
    " LIMITED.",
    " LTD.",
    " PLC",
    " PUBLIC LIMITED COMPANY",
    " DESIGNATED ACTIVITY COMPANY",
    " DAC",
    " COMPANY LIMITED BY GUARANTEE",
)


def normalize_company_name(
    name: str | None,
) -> str:

    if not name:
        return ""

    value = (
        str(name)
        .upper()
        .strip()
    )

    for suffix in LEGAL_SUFFIXES:

        if value.endswith(suffix):

            value = value[
                : -len(suffix)
            ].strip()

            break

    value = re.sub(
        r"[^A-Z0-9 ]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ======================================================================
# COMPANY NAME MATCHING
# ======================================================================

def company_name_tokens(
    name: str | None,
) -> set[str]:

    normalized = normalize_company_name(
        name
    )

    if not normalized:
        return set()

    stop_words = {
        "LIMITED",
        "LTD",
        "COMPANY",
        "THE",
        "IRELAND",
        "IRISH",
    }

    return {
        token
        for token in normalized.split()
        if len(token) >= 2
        and token not in stop_words
    }


def company_match_score(
    company_name: str,
    candidate_text: str,
) -> int:

    company_tokens = company_name_tokens(
        company_name
    )

    if not company_tokens:
        return 0

    candidate_normalized = normalize_company_name(
        candidate_text
    )

    candidate_tokens = set(
        candidate_normalized.split()
    )

    if not candidate_tokens:
        return 0

    matched = (
        company_tokens
        & candidate_tokens
    )

    ratio = (
        len(matched)
        / len(company_tokens)
    )

    return int(
        ratio * 100
    )


# ======================================================================
# WEBSITE DISCOVERY
# ======================================================================

def discover_company_website(
    company_name: str,
    country: str | None = None,
) -> tuple[str | None, list[dict]]:
    """
    Resolve the company's official website through the canonical
    EmployerResolver.

    EmployerResolver is responsible for:

        - Brave discovery
        - candidate ranking
        - blocked-domain filtering
        - first-party identity verification
        - rejecting directories / registries / social sites
        - returning None when identity cannot be established

    The country argument is retained for API compatibility with the
    previous enrichment implementation.

    Returns:

        (
            verified_website,
            evidence
        )

    The resolver currently returns the verified website itself.
    Evidence is represented here as a compact pipeline record so that
    downstream callers can continue receiving the same tuple shape.
    """

    print(
        f"[ENRICH] Resolving official website "
        f"for {company_name}"
    )

    try:
        resolver = EmployerResolver()

    except Exception as exc:

        print(
            f"[ENRICH] Employer resolver unavailable: "
            f"{exc}"
        )

        return None, []

    search_name = normalize_company_name(
        company_name
    )

    if not search_name:
        print(
            '[ENRICH] Cannot resolve official website: '
            'company name is empty'
        )
        return None, []

    if search_name != str(company_name).strip().upper():
        print(
            f'[ENRICH] Search identity: '
            f'{search_name}'
        )

    try:
        website = resolver.resolve(
            search_name
        )

    except Exception as exc:

        print(
            f"[ENRICH] Employer resolver failed "
            f"for {company_name}: {exc}"
        )

        return None, []

    if not website:

        print(
            f"[ENRICH] No verified official "
            f"website found for {company_name}"
        )

        return None, []

    website = normalize_url(
        website
    )

    if not website:

        return None, []

    evidence = [
        {
            "url": website,
            "title": "",
            "description": "",
            "score": 100,
            "query": "EmployerResolver",
            "source": "EmployerResolver",
            "verified": True,
        }
    ]

    print(
        f"[ENRICH] VERIFIED official website: "
        f"{website}"
    )

    return website, evidence


# ======================================================================
# WEBSITE PAGE DISCOVERY
# ======================================================================

COMMON_COMPANY_PATHS = [
    "",
    "/about",
    "/about-us",
    "/company",
    "/our-company",
    "/who-we-are",
    "/about-company",
]


def collect_company_pages(
    website: str,
) -> list[tuple[str, str]]:

    pages = []

    base = normalize_url(
        website
    )

    if not base:
        return pages

    seen = set()

    for path in COMMON_COMPANY_PATHS:

        url = (
            base + path
        )

        if url in seen:
            continue

        seen.add(url)

        html = fetch_page(
            url
        )

        if not html:
            continue

        text = html_to_text(
            html
        )

        if not text:
            continue

        pages.append(
            (
                url,
                text,
            )
        )

    return pages


# ======================================================================
# INDUSTRY DETECTION
# ======================================================================

INDUSTRY_KEYWORDS = {

    "healthtech": [
        "healthcare",
        "health technology",
        "medical software",
        "clinical",
        "life sciences",
        "biotech",
        "pharmaceutical",
        "drug discovery",
        "healthtech",
    ],

    "fintech": [
        "fintech",
        "financial technology",
        "payments",
        "banking platform",
        "financial services",
        "lending",
        "insurtech",
    ],

    "saas": [
        "saas",
        "software as a service",
        "cloud software",
        "software platform",
        "subscription software",
    ],

    "software": [
        "software development",
        "software company",
        "software platform",
        "technology platform",
        "enterprise software",
        "application software",
    ],

    "ai": [
        "artificial intelligence",
        "machine learning",
        "generative ai",
        "ai platform",
        "deep learning",
        "computer vision",
        "natural language processing",
    ],

    "cybersecurity": [
        "cybersecurity",
        "cyber security",
        "information security",
        "security platform",
        "threat detection",
        "identity security",
    ],

    "cloud": [
        "cloud computing",
        "cloud infrastructure",
        "cloud platform",
        "cloud services",
        "cloud engineering",
        "kubernetes",
        "container platform",
    ],

    "technology": [
        "technology company",
        "technology platform",
        "digital platform",
        "digital transformation",
        "technology services",
        "it services",
    ],

    "consulting": [
        "management consulting",
        "technology consulting",
        "business consulting",
        "advisory services",
        "consultancy",
    ],
}


def detect_industry(
    text: str,
) -> str | None:

    normalized = text.lower()

    scores = {}

    for industry, keywords in (
        INDUSTRY_KEYWORDS.items()
    ):

        score = 0

        for keyword in keywords:

            if keyword in normalized:
                score += 1

        if score:
            scores[
                industry
            ] = score

    if not scores:
        return None

    return max(
        scores,
        key=scores.get,
    )


# ======================================================================
# EMPLOYEE EXTRACTION
# ======================================================================

def extract_employee_count(
    text: str,
) -> int | None:

    patterns = [

        r"(\d[\d,]*)\s*(?:\+)?\s*employees",

        r"team of\s+(\d[\d,]*)",

        r"(\d[\d,]*)\s*(?:people|staff)\s+"
        r"(?:across|worldwide|globally)",

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = (
            match.group(1)
            .replace(",", "")
        )

        try:

            return int(
                value
            )

        except ValueError:
            continue

    return None


# ======================================================================
# DESCRIPTION EXTRACTION
# ======================================================================

def extract_description(
    text: str,
) -> str | None:

    if not text:
        return None

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    useful = []

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 50:
            continue

        lower = sentence.lower()

        if any(
            keyword in lower
            for keyword in (
                "we are",
                "we provide",
                "we build",
                "we develop",
                "our company",
                "our platform",
                "our mission",
                "company",
                "technology",
                "software",
            )
        ):
            useful.append(
                sentence
            )

        if len(useful) >= 2:
            break

    if not useful:
        return text[:500]

    return " ".join(
        useful
    )[:800]


# ======================================================================
# COUNTRY DETECTION
# ======================================================================

def detect_country(
    text: str,
) -> str | None:

    normalized = text.lower()

    if (
        "ireland" in normalized
        or "dublin" in normalized
        or "cork" in normalized
        or "galway" in normalized
    ):
        return "Ireland"

    if (
        "united kingdom" in normalized
        or "london" in normalized
        or "england" in normalized
    ):
        return "United Kingdom"

    if (
        "united states" in normalized
        or "new york" in normalized
        or "california" in normalized
    ):
        return "United States"

    return None


# ======================================================================
# ENRICH CANDIDATE
# ======================================================================

def enrich_candidate(
    candidate: DiscoveryCandidate,
) -> DiscoveryCandidate:
    """
    Main enrichment entry point.

    Existing website:
        Validate/use supplied website and enrich it.

    Missing website:
        Use EmployerResolver to discover and strictly verify the
        official website.

    Website absence does NOT cause rejection.

    Companies without websites remain eligible for:

        - founder research
        - director research
        - contact research
        - other registry intelligence
    """

    company_name = (
        candidate.company_name
        or ""
    ).strip()

    if not company_name:
        return candidate

    print()

    print(
        f"[ENRICH] Enriching company: "
        f"{company_name}"
    )

    website = normalize_url(
        candidate.website
    )

    discovery_evidence = []

    # ------------------------------------------------------------------
    # STEP 1 — Discover website if missing
    # ------------------------------------------------------------------

    if not website:

        website, discovery_evidence = (
            discover_company_website(
                company_name=company_name,
                country=candidate.country,
            )
        )

    else:

        print(
            f"[ENRICH] Existing website: "
            f"{website}"
        )

    # ------------------------------------------------------------------
    # STEP 2 — No website
    # ------------------------------------------------------------------

    if not website:

        print(
            f"[ENRICH] Website not established "
            f"for {company_name}"
        )

        print(
            "[ENRICH] Company remains eligible "
            "for founder/director research."
        )

        return candidate

    # ------------------------------------------------------------------
    # STEP 3 — Website pages
    # ------------------------------------------------------------------

    pages = collect_company_pages(
        website
    )

    if not pages:

        print(
            "[ENRICH] Website found but "
            "no readable pages were retrieved."
        )

        return candidate.model_copy(
            update={
                "website": website,
                "source_url": (
                    candidate.source_url
                    or website
                ),
                "confidence": max(
                    candidate.confidence,
                    70,
                ),
            }
        )

    combined_text = " ".join(
        text
        for _, text in pages
    )

    # ------------------------------------------------------------------
    # STEP 4 — Industry
    # ------------------------------------------------------------------

    industry = detect_industry(
        combined_text
    )

    if industry:

        print(
            f"[ENRICH] Industry: "
            f"{industry}"
        )

    else:

        print(
            "[ENRICH] Industry: "
            "not established"
        )

    # ------------------------------------------------------------------
    # STEP 5 — Employee count
    # ------------------------------------------------------------------

    employee_count = (
        extract_employee_count(
            combined_text
        )
    )

    if employee_count is not None:

        print(
            f"[ENRICH] Employee count: "
            f"{employee_count}"
        )

    else:

        print(
            "[ENRICH] Employee count: "
            "not established"
        )

    # ------------------------------------------------------------------
    # STEP 6 — Description
    # ------------------------------------------------------------------

    description = extract_description(
        combined_text
    )

    if description:

        print(
            "[ENRICH] Official company "
            "description established"
        )

    else:

        print(
            "[ENRICH] Description: "
            "not established"
        )

    # ------------------------------------------------------------------
    # STEP 7 — Country
    # ------------------------------------------------------------------

    country = (
        candidate.country
        or detect_country(
            combined_text
        )
    )

    # ------------------------------------------------------------------
    # STEP 8 — Confidence
    # ------------------------------------------------------------------

    confidence = 50

    if website:
        confidence += 25

    if industry:
        confidence += 10

    if description:
        confidence += 10

    if employee_count is not None:
        confidence += 5

    confidence = min(
        confidence,
        100,
    )

    print(
        f"[ENRICH] Enrichment confidence: "
        f"{confidence}"
    )

    # ------------------------------------------------------------------
    # STEP 9 — Return enriched candidate
    # ------------------------------------------------------------------

    return candidate.model_copy(
        update={

            "website": website,

            "country": country,

            "industry": (
                industry
                or candidate.industry
            ),

            "employee_count": (
                employee_count
                if employee_count is not None
                else candidate.employee_count
            ),

            "description": (
                description
                or candidate.description
            ),

            "source_url": (
                candidate.source_url
                or website
            ),

            "confidence": confidence,
        }
    )


# ======================================================================
# OPTIONAL CLASS WRAPPER
# ======================================================================

class CompanyEnrichment:
    """
    Small class wrapper for future pipeline integration.
    """

    def enrich(
        self,
        candidate: DiscoveryCandidate,
    ) -> DiscoveryCandidate:

        return enrich_candidate(
            candidate
        )