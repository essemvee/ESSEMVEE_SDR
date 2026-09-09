from app.services.signal_extractor import (
    extract_signal_from_result,
)


results = [
    {
        "title": (
            "Senior DevOps Engineer - "
            "Example Company"
        ),
        "url": (
            "https://example.com/careers/devops"
        ),
        "description": (
            "Example Company is hiring a "
            "Senior DevOps Engineer with "
            "Azure, Terraform and Kubernetes "
            "experience."
        ),
    },
    {
        "title": (
            "How to Become a DevOps Engineer "
            "in Ireland"
        ),
        "url": (
            "https://oiliuna.ie/how-to-become"
        ),
        "description": (
            "Learn how to become a DevOps "
            "Engineer in Ireland."
        ),
    },
]


print()
print("==============================")
print("ESSEMVEE SIGNAL EXTRACTION")
print("==============================")
print()


for result in results:

    signal = extract_signal_from_result(
        company_name="Test Company",
        result=result,
    )

    print(
        f"Title: {result['title']}"
    )

    print(
        f"Type: {signal.signal_type}"
    )

    print(
        f"Strength: {signal.strength}/100"
    )

    print()