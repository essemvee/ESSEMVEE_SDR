from app.services.web_discovery import WebDiscoverySource


source = WebDiscoverySource()

company = "Deciphex"

queries = [
    '"Deciphex" website',
    '"Deciphex" careers',
    '"Deciphex" Ireland',
]


print()
print("==============================")
print("ESSEMVEE EMPLOYER SEARCH DEBUG")
print("==============================")
print()


for query in queries:

    print()
    print(
        f"QUERY: {query}"
    )
    print(
        "------------------------------"
    )

    results = source.search(
        query=query,
        count=10,
    )

    print(
        f"Results: {len(results)}"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        print()
        print(
            f"{index}. "
            f"{result.get('title')}"
        )

        print(
            f"URL: "
            f"{result.get('url')}"
        )

        print(
            f"Description: "
            f"{result.get('description')}"
        )