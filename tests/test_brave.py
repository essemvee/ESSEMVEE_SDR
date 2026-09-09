from app.services.web_discovery import (
    WebDiscoverySource,
)


source = WebDiscoverySource()


query = '"DevOps Engineer" Ireland'


results = source.search(
    query=query,
    count=5,
)


print()
print("========================================")
print("       ESSEMVEE BRAVE SEARCH TEST")
print("========================================")
print()

print(f"Query: {query}")
print(f"Results returned: {len(results)}")

print()

for index, result in enumerate(
    results,
    start=1,
):

    print(
        f"{index}. "
        f"{result.get('title', 'No title')}"
    )

    print(
        f"   URL: "
        f"{result.get('url', 'No URL')}"
    )

    print(
        f"   Description: "
        f"{result.get('description', 'No description')}"
    )

    print()