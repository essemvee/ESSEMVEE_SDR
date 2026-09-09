from app.services.result_filter import (
    filter_search_results,
)


results = [
    {
        "title": "LinkedIn DevOps Jobs",
        "url": "https://ie.linkedin.com/jobs/devops-engineer-jobs",
        "description": "DevOps jobs in Ireland",
    },
    {
        "title": "Indeed DevOps Jobs",
        "url": "https://ie.indeed.com/q-devops-engineer-jobs.html",
        "description": "DevOps jobs",
    },
    {
        "title": "Example Company Careers",
        "url": "https://example-company.com/careers",
        "description": "Senior DevOps Engineer",
    },
]


filtered = filter_search_results(
    results
)


print()
print("==============================")
print("ESSEMVEE RESULT FILTER")
print("==============================")
print()

print(
    f"Results received: {len(results)}"
)

print(
    f"Results after filtering: "
    f"{len(filtered)}"
)

for result in filtered:

    print()
    print(
        f"Title: {result['title']}"
    )

    print(
        f"URL: {result['url']}"
    )