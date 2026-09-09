from app.services.employer_resolver import (
    EmployerResolver,
    canonicalize_url,
    extract_domain,
    is_blocked_domain,
    score_result,
    verify_employer_website,
)


def inspect_company(resolver, company_name):
    print()
    print("=" * 100)
    print(f"COMPANY: {company_name}")
    print("=" * 100)

    queries = [
        f'"{company_name}" website',
        f'"{company_name}" careers',
        f'"{company_name}" Ireland',
    ]

    candidates = []

    for query in queries:
        print()
        print(f"QUERY: {query}")
        print("-" * 100)

        try:
            results = resolver.discovery_source.search(
                query,
                count=10,
            )
        except Exception as exc:
            print(f"SEARCH ERROR: {exc}")
            continue

        for result in results:
            url = result.get("url") or ""
            title = result.get("title") or ""
            description = result.get("description") or ""

            if not url:
                continue

            blocked = is_blocked_domain(url)
            score = score_result(company_name, result)

            print()
            print(f"TITLE: {title}")
            print(f"URL: {url}")
            print(f"SCORE: {score}")
            print(f"BLOCKED: {blocked}")

            if blocked or score < 50:
                continue

            canonical = canonicalize_url(url)

            if not canonical:
                continue

            candidates.append(canonical)

    print()
    print("-" * 100)
    print("CANDIDATE VERIFICATION")
    print("-" * 100)

    seen = set()

    for website in candidates:
        domain = extract_domain(website)

        if not domain or domain in seen:
            continue

        seen.add(domain)

        verified = verify_employer_website(
            company_name,
            website,
        )

        print()
        print(f"COMPANY: {company_name}")
        print(f"DOMAIN: {domain}")
        print(f"WEBSITE: {website}")
        print(f"VERIFIED: {verified}")

    print()
    print("-" * 100)

    resolved = resolver.resolve(company_name)

    print(f"FINAL RESOLVER RESULT: {resolved}")


def main():
    resolver = EmployerResolver()

    inspect_company(
        resolver,
        "House Surveys",
    )

    inspect_company(
        resolver,
        "Deciphex",
    )


if __name__ == "__main__":
    main()