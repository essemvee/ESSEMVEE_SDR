from app.models.discovery import (
    DiscoveryCandidate,
)

from app.models.signal import Signal

from app.services.pipeline import (
    build_company_input,
)


candidate = DiscoveryCandidate(
    company_name="Example SaaS",
    website="https://example.com",
    country="Ireland",
    industry="B2B SaaS",
    employee_count=120,
    description=(
        "A growing B2B SaaS company "
        "serving European businesses."
    ),
    discovery_source="Company website",
    source_url="https://example.com",
    confidence=90,
)


signals = [
    Signal(
        signal_type="Hiring",
        title="Senior DevOps Engineer",
        description=(
            "The company is hiring a "
            "Senior DevOps Engineer."
        ),
        source="Company careers page",
        source_url=(
            "https://example.com/careers"
        ),
        detected_date="2026-08-13",
        strength=90,
    ),
    Signal(
        signal_type="Cloud",
        title="Azure experience required",
        description=(
            "An engineering role requires "
            "Azure experience."
        ),
        source="Company careers page",
        source_url=(
            "https://example.com/careers"
        ),
        detected_date="2026-08-13",
        strength=90,
    ),
]


company = build_company_input(
    candidate,
    signals,
)


print()
print("==============================")
print("ESSEMVEE PIPELINE")
print("==============================")
print()

print(
    f"Company: {company.company_name}"
)

print(
    f"Country: {company.country}"
)

print(
    f"Industry: {company.industry}"
)

print(
    f"Employees: "
    f"{company.employee_count}"
)

print(
    f"Signals: "
    f"{len(company.signals)}"
)

for signal in company.signals:

    print(
        f"- {signal.signal_type}: "
        f"{signal.description}"
    )

print()
print("Pipeline input ready.")