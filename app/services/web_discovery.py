import os

import requests
from dotenv import load_dotenv

from app.models.discovery import (
    DiscoveryCandidate,
    DiscoveryResult,
)
from app.services.source import DiscoverySource


load_dotenv()


class WebDiscoverySource(DiscoverySource):
    """
    Brave Search-backed discovery source.

    V1 responsibility:
    - Run a web search
    - Return raw search results
    - Preserve URLs and descriptions as evidence
    """

    BASE_URL = (
        "https://api.search.brave.com/"
        "res/v1/web/search"
    )

    def __init__(self):

        self.api_key = os.getenv(
            "BRAVE_SEARCH_API_KEY"
        )

        if not self.api_key:
            raise RuntimeError(
                "BRAVE_SEARCH_API_KEY is missing "
                "from .env"
            )

    def search(
        self,
        query: str,
        count: int = 10,
    ) -> list[dict]:

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }

        params = {
            "q": query,
            "search_lang": "en",
            "count": min(count, 20),
        }

        response = requests.get(
            self.BASE_URL,
            headers=headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data
            .get("web", {})
            .get("results", [])
        )

    def discover(
        self,
        query: str,
    ) -> DiscoveryResult:

        results = self.search(
            query=query,
            count=10,
        )

        candidates = []

        for result in results:

            title = result.get(
                "title",
                "",
            )

            url = result.get(
                "url",
            )

            description = result.get(
                "description",
                "",
            )

            if not title:
                continue

            candidates.append(
                DiscoveryCandidate(
                    company_name=title,
                    website=url,
                    country="Ireland",
                    description=description,
                    discovery_source=(
                        "Brave Search"
                    ),
                    source_url=url,
                    confidence=50,
                )
            )

        return DiscoveryResult(
            candidates=candidates
        )