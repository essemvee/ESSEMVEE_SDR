from app.services.company_extractor import (
    extract_company_from_result,
)


results = [
    {
        "title": (
            "Senior DevOps Engineer "
            "(Ireland based) at Deciphex"
        ),
        "url": (
            "https://jobgether.com/offer/"
            "69a0d7b17f0cfae7f11efa47-"
            "senior-devops-engineer"
        ),
        "description": (
            "Senior DevOps Engineer "
            "Ireland based at Deciphex."
        ),
    },
    {
        "title": (
            "Senior DevOps Engineer - "
            "Beyond, Inc. | Built In"
        ),
        "url": (
            "https://builtin.com/job/"
            "senior-devops-engineer-ireland/"
        ),
        "description": (
            "Senior DevOps Engineer "
            "at Beyond, Inc."
        ),
    },
]


print()
print("==============================")
print("ESSEMVEE COMPANY EXTRACTION")
print("==============================")
print()


for result in results:

    company = extract_company_from_result(
        result
    )

    print(
        f"Title: {result['title']}"
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
            "Company: Not identified"
        )

    print()