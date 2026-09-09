from app.services.prospect_discovery import (
    ProspectDiscovery,
)


discovery = ProspectDiscovery()


query = (
    '"Senior DevOps Engineer" '
    '"Ireland" '
    '-LinkedIn '
    '-Indeed '
    '-Glassdoor '
    '-IrishJobs'
)


prospects = discovery.discover(
    query=query,
    count=5,
)


print()
print("========================================")
print("       ESSEMVEE PROSPECT DISCOVERY")
print("========================================")
print()

print(f"Query: {query}")
print(
    f"Prospects discovered: "
    f"{len(prospects)}"
)

for index, (
    company,
    signal,
) in enumerate(
    prospects,
    start=1,
):

    print()
    print(
        f"---------- PROSPECT {index} ----------"
    )

    print(
        f"Company: "
        f"{company.company_name}"
    )

    print(
        f"Website: "
        f"{company.website}"
    )

    print(
        f"Country: "
        f"{company.country}"
    )

    print(
        f"Discovery Source: "
        f"{company.discovery_source}"
    )

    print(
        f"Evidence URL: "
        f"{signal.source_url}"
    )

    print(
        f"Signal Type: "
        f"{signal.signal_type}"
    )

    print(
        f"Signal: "
        f"{signal.title}"
    )

    print(
        f"Strength: "
        f"{signal.strength}/100"
    )

print()
print("========================================")