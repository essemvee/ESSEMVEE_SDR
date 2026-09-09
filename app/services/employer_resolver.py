from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import requests

from app.services.web_discovery import WebDiscoverySource


# ============================================================================
# CONFIGURATION
# ============================================================================

REQUEST_TIMEOUT = 12

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}


# ============================================================================
# DOMAINS THAT ARE NEVER FIRST-PARTY COMPANY WEBSITES
# ============================================================================
#
# These sites are useful discovery sources but must never become the official
# company website.
#
# IMPORTANT:
# Domain matching below is boundary-aware. Therefore:
#
#     x.com          -> blocked
#     linkedin.com   -> blocked
#     deciphex.com   -> NOT blocked
#
# We do NOT use simple substring matching for domains.
# ============================================================================

BLOCKED_DOMAINS = {
    # Government / registries
    "find-and-update.company-information.service.gov.uk",
    "companieshouse.gov.uk",
    "cro.ie",
    "opendata.cro.ie",

    # Business intelligence / company databases
    "crunchbase.com",
    "zoominfo.com",
    "apollo.io",
    "lusha.com",
    "rocketreach.co",
    "signalhire.com",
    "theorg.com",
    "dnb.com",
    "datanyze.com",
    "owler.com",
    "bizapedia.com",
    "corporationwiki.com",
    "companyhouse.co.uk",
    "companycheck.co.uk",
    "192.com",
    "kompass.com",
    "brownbook.net",
    "hotfrog.com",
    "bizcommunity.com",
    "bdtradeinfo.com",
    "tracxn.com",

    # Job boards / recruitment
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "irishjobs.ie",
    "jobs.ie",
    "monster.com",
    "ziprecruiter.com",
    "talent.com",
    "jobserve.com",
    "workable.com",
    "greenhouse.io",
    "lever.co",
    "smartrecruiters.com",
    "builtin.com",
    "dynamitejobs.com",

    # Social media
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
    "reddit.com",

    # News / media
    "prnewswire.com",
    "businesswire.com",
    "globenewswire.com",
    "reuters.com",
    "forbes.com",
    "medium.com",
    "siliconrepublic.com",

    # Reviews / listings
    "trustpilot.com",
    "tripadvisor.com",
    "yelp.com",
    "checkatrade.com",

    # Hosted site platforms
    "wixsite.com",
    "wordpress.com",
    "blogspot.com",
    "weebly.com",
    "sites.google.com",
}


# ============================================================================
# GENERIC COMPANY WORDS
# ============================================================================

GENERIC_COMPANY_WORDS = {
    "limited",
    "ltd",
    "limitedcompany",
    "company",
    "co",
    "plc",
    "llc",
    "inc",
    "incorporated",
    "corp",
    "corporation",
    "group",
    "holdings",
    "holding",
    "international",
    "global",
    "ireland",
    "uk",
    "usa",
    "europe",
    "services",
    "service",
    "solutions",
    "consulting",
    "consultancy",
    "technologies",
    "technology",
    "systems",
    "software",
    "digital",
    "business",
    "partners",
    "partner",
    "management",
    "development",
    "developments",
}


# ============================================================================
# NORMALIZATION
# ============================================================================

def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()
    value = value.replace("&", " and ")

    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


def normalize_company_name(company_name: str | None) -> str:
    return normalize_text(company_name).replace(" ", "")


def company_words(company_name: str | None) -> list[str]:
    normalized = normalize_text(company_name)

    if not normalized:
        return []

    words = normalized.split()

    return [
        word
        for word in words
        if word not in GENERIC_COMPANY_WORDS
        and len(word) >= 3
    ]


# ============================================================================
# GENERIC-NAME DETECTION
# ============================================================================

def is_generic_company_name(company_name: str) -> bool:
    """
    Determine whether a company name is primarily composed of generic
    industry/business terminology.

    Example:

        House Surveys
        Technology Services
        Business Solutions

    should receive stricter verification than:

        Deciphex
        Vercel
        Stripe
    """

    words = normalize_text(company_name).split()

    if not words:
        return True

    distinctive = company_words(company_name)

    # No distinctive words means the name is highly generic.
    if not distinctive:
        return True

    # If the name has only one distinctive word and it is a common
    # business/service term, treat it conservatively.
    if len(distinctive) == 1:
        common_terms = {
            "survey",
            "surveys",
            "software",
            "digital",
            "systems",
            "technology",
            "technologies",
            "consulting",
            "consultancy",
            "services",
            "solutions",
            "development",
            "developments",
            "management",
            "business",
            "property",
            "investments",
            "investment",
            "capital",
            "engineering",
            "analytics",
            "marketing",
            "design",
        }

        if distinctive[0] in common_terms:
            return True

    return False


# ============================================================================
# DOMAIN HELPERS
# ============================================================================

def extract_domain(url: str | None) -> str | None:
    if not url:
        return None

    url = url.strip()

    if not url:
        return None

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)

        hostname = parsed.hostname

        if not hostname:
            return None

        hostname = hostname.lower().rstrip(".")

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    except Exception:
        return None


def canonicalize_url(url: str | None) -> str | None:
    domain = extract_domain(url)

    if not domain:
        return None

    return f"https://{domain}"


def domain_matches_blocked(domain: str, blocked_domain: str) -> bool:
    """
    Boundary-aware domain matching.

    Correct:

        linkedin.com
        www.linkedin.com
        jobs.linkedin.com

    Incorrect:

        mylinkedin.com
        deciphex.com for x.com
    """

    domain = domain.lower().rstrip(".")
    blocked_domain = blocked_domain.lower().rstrip(".")

    return (
        domain == blocked_domain
        or domain.endswith("." + blocked_domain)
    )


def is_blocked_domain(url: str | None) -> bool:
    domain = extract_domain(url)

    if not domain:
        return True

    for blocked_domain in BLOCKED_DOMAINS:
        if domain_matches_blocked(
            domain,
            blocked_domain,
        ):
            return True

    return False


# ============================================================================
# HOMEPAGE FETCHING
# ============================================================================

def fetch_homepage(
    website: str,
) -> tuple[str, str, str]:
    """
    Return:

        title
        visible page text
        final URL after redirects
    """

    try:
        response = requests.get(
            website,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        if response.status_code >= 400:
            return "", "", response.url

        content_type = response.headers.get(
            "content-type",
            "",
        ).lower()

        if "text/html" not in content_type:
            return "", "", response.url

        html = response.text[:2_000_000]

        title_match = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        title = ""

        if title_match:
            title = re.sub(
                r"\s+",
                " ",
                title_match.group(1),
            ).strip()

        # Remove scripts and styles.
        text = re.sub(
            r"<script\b[^>]*>.*?</script>",
            " ",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        text = re.sub(
            r"<style\b[^>]*>.*?</style>",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # Remove HTML tags.
        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        # Basic HTML entity handling.
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return title, text, response.url

    except requests.RequestException:
        return "", "", website

    except Exception:
        return "", "", website


# ============================================================================
# IDENTITY SIGNALS
# ============================================================================

def identity_signals(
    company_name: str,
    website: str,
    title: str,
    page_text: str,
) -> tuple[int, list[str]]:
    """
    Evaluate first-party identity evidence.

    This function deliberately distinguishes:

        generic phrase matching

    from:

        actual company identity.

    Returning a high score requires multiple independent signals.
    """

    normalized_company = normalize_text(company_name)
    compact_company = normalize_company_name(company_name)

    normalized_title = normalize_text(title)
    normalized_page = normalize_text(page_text)

    if not normalized_company:
        return 0, []

    words = company_words(company_name)

    evidence: list[str] = []
    score = 0

    # ------------------------------------------------------------------
    # Exact company name
    # ------------------------------------------------------------------

    exact_in_title = (
        normalized_company in normalized_title
    )

    exact_in_page = (
        normalized_company in normalized_page
    )

    if exact_in_title:
        score += 45
        evidence.append("EXACT_NAME_IN_TITLE")

    if exact_in_page:
        score += 30
        evidence.append("EXACT_NAME_IN_PAGE")

    # ------------------------------------------------------------------
    # Distinctive words
    # ------------------------------------------------------------------

    if words:
        matched_words = [
            word
            for word in words
            if word in normalized_page
        ]

        if len(words) >= 2:
            if len(matched_words) == len(words):
                score += 20
                evidence.append(
                    "ALL_DISTINCTIVE_WORDS_IN_PAGE"
                )

            elif len(matched_words) >= 2:
                score += 8
                evidence.append(
                    "MULTIPLE_DISTINCTIVE_WORDS_IN_PAGE"
                )

        elif len(words) == 1:
            if words[0] in normalized_title:
                score += 10
                evidence.append(
                    "DISTINCTIVE_WORD_IN_TITLE"
                )

    # ------------------------------------------------------------------
    # Domain relationship
    # ------------------------------------------------------------------

    domain = extract_domain(website)

    if domain:
        normalized_domain = normalize_text(domain)
        compact_domain = normalized_domain.replace(
            " ",
            "",
        )

        if (
            compact_company
            and compact_company in compact_domain
        ):
            score += 40
            evidence.append("COMPANY_NAME_IN_DOMAIN")

        elif words:
            domain_matches = [
                word
                for word in words
                if word in normalized_domain
            ]

            if len(domain_matches) >= 2:
                score += 25
                evidence.append(
                    "MULTIPLE_COMPANY_WORDS_IN_DOMAIN"
                )

            elif len(domain_matches) == 1:
                score += 5
                evidence.append(
                    "COMPANY_WORD_IN_DOMAIN"
                )

    # ------------------------------------------------------------------
    # First-party business context
    # ------------------------------------------------------------------

    context_patterns = (
        "about us",
        "about company",
        "our company",
        "who we are",
        "contact us",
        "get in touch",
        "head office",
        "registered office",
        "our services",
        "our team",
        "privacy policy",
        "terms and conditions",
    )

    context_matches = sum(
        1
        for pattern in context_patterns
        if normalize_text(pattern) in normalized_page
    )

    if context_matches >= 3:
        score += 10
        evidence.append("FIRST_PARTY_CONTEXT")

    return min(score, 100), evidence


# ============================================================================
# OFFICIAL WEBSITE VERIFICATION
# ============================================================================

def verify_employer_website(
    company_name: str,
    website: str,
) -> bool:
    """
    Strict first-party website verification.

    False negatives are preferable to false positives.

    A website is NOT accepted merely because it discusses the same subject
    as the company name.
    """

    if not company_name or not website:
        return False

    canonical = canonicalize_url(website)

    if not canonical:
        return False

    if is_blocked_domain(canonical):
        return False

    title, page_text, final_url = fetch_homepage(
        canonical
    )

    if not title and not page_text:
        return False

    # Redirecting to a blocked site invalidates the candidate.
    if is_blocked_domain(final_url):
        return False

    original_domain = extract_domain(canonical)
    final_domain = extract_domain(final_url)

    if not original_domain or not final_domain:
        return False

    score, evidence = identity_signals(
        company_name,
        canonical,
        title,
        page_text,
    )

    generic_name = is_generic_company_name(
        company_name
    )

    evidence_set = set(evidence)

    # ==================================================================
    # DISTINCTIVE COMPANY NAME
    # ==================================================================

    if not generic_name:

        # A distinctive company name appearing in the domain plus
        # supporting first-party evidence is strong.
        if (
            "COMPANY_NAME_IN_DOMAIN" in evidence_set
            and (
                "EXACT_NAME_IN_TITLE" in evidence_set
                or "EXACT_NAME_IN_PAGE" in evidence_set
            )
        ):
            return True

        # Exact company name in title + page is also strong.
        if (
            "EXACT_NAME_IN_TITLE" in evidence_set
            and "EXACT_NAME_IN_PAGE" in evidence_set
            and score >= 65
        ):
            return True

        # Distinctive multi-word identity with strong corroboration.
        if (
            "ALL_DISTINCTIVE_WORDS_IN_PAGE"
            in evidence_set
            and (
                "EXACT_NAME_IN_TITLE"
                in evidence_set
                or "COMPANY_NAME_IN_DOMAIN"
                in evidence_set
            )
            and score >= 65
        ):
            return True

        return False

    # ==================================================================
    # GENERIC COMPANY NAME
    # ==================================================================
    #
    # Generic names require substantially stronger evidence.
    #
    # Example:
    #
    #     House Surveys
    #
    # should not be accepted merely because a surveying website contains
    # the words "house surveys".
    # ==================================================================

    if generic_name:

        # Exact legal/business name in title AND page.
        if (
            "EXACT_NAME_IN_TITLE" in evidence_set
            and "EXACT_NAME_IN_PAGE" in evidence_set
            and score >= 75
        ):
            return True

        # Full company name in domain + exact identity on page/title.
        if (
            "COMPANY_NAME_IN_DOMAIN" in evidence_set
            and (
                "EXACT_NAME_IN_TITLE" in evidence_set
                or "EXACT_NAME_IN_PAGE" in evidence_set
            )
            and score >= 70
        ):
            return True

        # Multiple distinctive words plus exact title.
        if (
            "ALL_DISTINCTIVE_WORDS_IN_PAGE"
            in evidence_set
            and "EXACT_NAME_IN_TITLE"
            in evidence_set
            and "FIRST_PARTY_CONTEXT"
            in evidence_set
            and score >= 75
        ):
            return True

        return False

    return False


# ============================================================================
# SEARCH RESULT SCORING
# ============================================================================

def score_result(
    company_name: str,
    result: dict[str, Any],
) -> int:
    """
    Rank a search result as a possible website.

    IMPORTANT:

        This function only ranks candidates.

        It does NOT prove official ownership.

        verify_employer_website() performs final verification.
    """

    url = result.get("url") or ""

    if not url:
        return 0

    if is_blocked_domain(url):
        return 0

    title = result.get("title") or ""
    description = result.get("description") or ""

    normalized_company = normalize_text(
        company_name
    )

    normalized_title = normalize_text(title)

    normalized_description = normalize_text(
        description
    )

    score = 0

    # ---------------------------------------------------------------
    # Exact company name in result title.
    # ---------------------------------------------------------------

    if (
        normalized_company
        and normalized_company in normalized_title
    ):
        score += 45

    # ---------------------------------------------------------------
    # Domain relationship.
    # ---------------------------------------------------------------

    domain = extract_domain(url)

    if domain:
        compact_domain = normalize_text(
            domain
        ).replace(" ", "")

        compact_company = normalize_company_name(
            company_name
        )

        if (
            compact_company
            and compact_company in compact_domain
        ):
            score += 45

        else:
            words = company_words(company_name)

            domain_matches = [
                word
                for word in words
                if word in normalize_text(domain)
            ]

            if len(domain_matches) >= 2:
                score += 25

            elif len(domain_matches) == 1:
                score += 5

    # ---------------------------------------------------------------
    # Description can help, but only weakly.
    # ---------------------------------------------------------------

    if (
        normalized_company
        and normalized_company in normalized_description
    ):
        score += 5

    return min(score, 100)


# ============================================================================
# EMPLOYER RESOLVER
# ============================================================================

class EmployerResolver:
    """
    Canonical employer website resolver.

    Discovery:
        Brave Search

    Final authority:
        Strict first-party website verification

    Returning None is valid and expected when no official website can be
    confidently established.
    """

    def __init__(
        self,
        discovery_source: WebDiscoverySource | None = None,
    ):
        self.discovery_source = (
            discovery_source
            or WebDiscoverySource()
        )

    def resolve(
        self,
        company_name: str,
    ) -> str | None:

        if not company_name:
            return None

        queries = [
            f'"{company_name}" website',
            f'"{company_name}" careers',
            f'"{company_name}" Ireland',
        ]

        candidates: list[dict[str, Any]] = []

        for query in queries:

            try:
                results = self.discovery_source.search(
                    query,
                    count=10,
                )

            except Exception:
                continue

            for result in results:

                url = result.get("url") or ""

                if not url:
                    continue

                if is_blocked_domain(url):
                    continue

                score = score_result(
                    company_name,
                    result,
                )

                if score < 50:
                    continue

                candidates.append(
                    {
                        "url": url,
                        "score": score,
                        "title": result.get(
                            "title",
                            "",
                        ),
                        "description": result.get(
                            "description",
                            "",
                        ),
                    }
                )

        # Highest-quality candidates first.
        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        seen_domains: set[str] = set()

        for candidate in candidates:

            url = candidate["url"]

            domain = extract_domain(url)

            if not domain:
                continue

            if domain in seen_domains:
                continue

            seen_domains.add(domain)

            canonical = canonicalize_url(url)

            if not canonical:
                continue

            # Final strict first-party verification.
            if verify_employer_website(
                company_name,
                canonical,
            ):
                return canonical

        return None