from app.services.web_discovery import (
    WebDiscoverySource,
)

from app.services.result_filter import (
    filter_search_results,
)

from app.services.company_extractor import (
    extract_company_from_result,
)

from app.services.signal_extractor import (
    extract_signal_from_result,
)

from app.services.employer_resolver import (
    EmployerResolver,
)


class ProspectDiscovery:

    def __init__(self):

        self.source = WebDiscoverySource()

        self.employer_resolver = (
            EmployerResolver()
        )

    def discover(
        self,
        query: str,
        count: int = 10,
    ):

        results = self.source.search(
            query=query,
            count=count,
        )

        print()
        print(
            f"[DEBUG] Brave results: "
            f"{len(results)}"
        )

        filtered = filter_search_results(
            results
        )

        print(
            f"[DEBUG] After filter: "
            f"{len(filtered)}"
        )

        prospects = []

        seen_companies = set()

        for index, result in enumerate(
            filtered,
            start=1,
        ):

            print()
            print(
                f"[DEBUG] RESULT {index}"
            )

            print(
                f"[DEBUG] Title: "
                f"{result.get('title')}"
            )

            print(
                f"[DEBUG] URL: "
                f"{result.get('url')}"
            )

            print(
                f"[DEBUG] Description: "
                f"{result.get('description')}"
            )

            # -------------------------------------------------
            # COMPANY EXTRACTION
            # -------------------------------------------------

            company = (
                extract_company_from_result(
                    result
                )
            )

            if not company:

                print(
                    "[DEBUG] REJECT: "
                    "no company"
                )

                continue

            print(
                f"[DEBUG] Company: "
                f"{company.company_name}"
            )

            print(
                f"[DEBUG] Confidence: "
                f"{company.confidence}"
            )

            # -------------------------------------------------
            # SIGNAL EXTRACTION
            # -------------------------------------------------

            signal = (
                extract_signal_from_result(
                    company_name=(
                        company.company_name
                    ),
                    result=result,
                )
            )

            if not signal:

                print(
                    "[DEBUG] REJECT: "
                    "no signal"
                )

                continue

            print(
                f"[DEBUG] Signal: "
                f"{signal.signal_type}"
            )

            print(
                f"[DEBUG] Strength: "
                f"{signal.strength}"
            )

            # -------------------------------------------------
            # ONLY ACCEPT REAL HIRING SIGNALS
            # -------------------------------------------------

            if (
                signal.signal_type
                != "Hiring"
            ):

                print(
                    "[DEBUG] REJECT: "
                    "not Hiring"
                )

                continue

            # -------------------------------------------------
            # COMPANY CONFIDENCE
            # -------------------------------------------------

            if company.confidence < 70:

                print(
                    "[DEBUG] REJECT: "
                    "confidence below 70"
                )

                continue

            # -------------------------------------------------
            # DUPLICATE COMPANY CHECK
            # -------------------------------------------------

            company_key = (
                company.company_name
                .strip()
                .lower()
            )

            if company_key in seen_companies:

                print(
                    "[DEBUG] REJECT: "
                    "duplicate company"
                )

                continue

            # -------------------------------------------------
            # EMPLOYER WEBSITE RESOLUTION
            # -------------------------------------------------

            print(
                f"[DEBUG] Resolving official "
                f"website for "
                f"{company.company_name}..."
            )

            employer_website = (
                self.employer_resolver.resolve(
                    company.company_name
                )
            )

            if employer_website:

                print(
                    f"[DEBUG] Official website: "
                    f"{employer_website}"
                )

                company.website = (
                    employer_website
                )

            else:

                print(
                    "[DEBUG] Official website: "
                    "UNVERIFIED"
                )

                company.website = None

            # -------------------------------------------------
            # RECORD COMPANY
            # -------------------------------------------------

            seen_companies.add(
                company_key
            )

            # -------------------------------------------------
            # ACCEPT PROSPECT
            # -------------------------------------------------

            prospects.append(
                (
                    company,
                    signal,
                )
            )

            print(
                "[DEBUG] ACCEPTED"
            )

        return prospects