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


source = WebDiscoverySource()

query = (
    '"Senior DevOps Engineer" '
    '"Ireland" '
    '-LinkedIn '
    '-Indeed '
    '-Glassdoor '
    '-IrishJobs'
)


results = source.search(
    query=query,
    count=10,
)


print()
print("========================================")
print("       ESSEMVEE DISCOVERY DEBUG")
print("========================================")
print()

print(
    f"RAW BRAVE RESULTS: {len(results)}"
)

print()

for index, result in enumerate(
    results,
    start=1,
):

    print(
        f"========== RAW RESULT {index} =========="
    )

    print(
        f"Title: {result.get('title')}"
    )

    print(
        f"URL: {result.get('url')}"
    )

    print(
        f"Description: "
        f"{result.get('description')}"
    )

    print()


filtered = filter_search_results(
    results
)


print()
print(
    f"AFTER FILTER: {len(filtered)}"
)
print()


for index, result in enumerate(
    filtered,
    start=1,
):

    print(
        f"========== FILTERED RESULT {index} =========="
    )

    print(
        f"Title: {result.get('title')}"
    )

    print(
        f"URL: {result.get('url')}"
    )

    print()


print()
print(
    "========== EXTRACTION =========="
)
print()


for index, result in enumerate(
    filtered,
    start=1,
):

    company = extract_company_from_result(
        result
    )

    signal = extract_signal_from_result(
        company_name=(
            company.company_name
            if company
            else "Unknown"
        ),
        result=result,
    )

    print(
        f"RESULT {index}"
    )

    if company:

        print(
            f"Company: "
            f"{company.company_name}"
        )

        print(
            f"Confidence: "
            f"{company.confidence}/100"
        )

    else:

        print(
            "Company: NONE"
        )

    if signal:

        print(
            f"Signal Type: "
            f"{signal.signal_type}"
        )

        print(
            f"Signal Strength: "
            f"{signal.strength}/100"
        )

    else:

        print(
            "Signal: NONE"
        )

    print()