from urllib.parse import urlparse


# Only block domains that are almost always
# generic job-search pages or social networks.
BLOCKED_DOMAINS = {
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
}


DISCUSSION_DOMAINS = {
    "reddit.com",
}


def get_domain(url: str) -> str:

    try:
        hostname = urlparse(url).hostname

        if not hostname:
            return ""

        hostname = hostname.lower()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    except Exception:
        return ""


def is_blocked_domain(url: str) -> bool:

    domain = get_domain(url)

    if not domain:
        return True

    for blocked in BLOCKED_DOMAINS:

        if (
            domain == blocked
            or domain.endswith("." + blocked)
        ):
            return True

    return False


def is_discussion_site(url: str) -> bool:

    domain = get_domain(url)

    for discussion_domain in DISCUSSION_DOMAINS:

        if (
            domain == discussion_domain
            or domain.endswith(
                "." + discussion_domain
            )
        ):
            return True

    return False


def filter_search_results(
    results: list[dict],
) -> list[dict]:

    filtered = []

    for result in results:

        url = result.get("url")

        if not url:
            continue

        # Remove obvious blocked sources.
        if is_blocked_domain(url):
            continue

        # Remove discussion/social content.
        if is_discussion_site(url):
            continue

        # Everything else continues to the
        # employer and signal validation layers.
        filtered.append(result)

    return filtered