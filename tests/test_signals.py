from app.models.signal import Signal

from app.services.signals import (
    normalize_signals,
)


signals = [
    Signal(
        signal_type="Hiring",
        title=" Senior DevOps Engineer ",
        description=(
            " Company is hiring a Senior "
            "DevOps Engineer with Azure experience. "
        ),
        source="Company careers page",
        source_url=" https://example.com/careers ",
        detected_date="2026-08-13",
        strength=90,
    ),
    Signal(
        signal_type="Hiring",
        title="Senior DevOps Engineer",
        description=(
            "Company is hiring a Senior "
            "DevOps Engineer with Azure experience."
        ),
        source="Company careers page",
        source_url="https://example.com/careers",
        detected_date="2026-08-13",
        strength=90,
    ),
]


result = normalize_signals(
    company_name="Example SaaS",
    signals=signals,
)


print()
print("==============================")
print("ESSEMVEE SIGNAL ENGINE")
print("==============================")
print()

print(
    f"Signals received: {len(signals)}"
)

print(
    f"Unique signals: "
    f"{len(result.signals)}"
)

for signal in result.signals:

    print()
    print(
        f"Type: {signal.signal_type}"
    )

    print(
        f"Title: {signal.title}"
    )

    print(
        f"Strength: {signal.strength}/100"
    )

    print(
        f"Source: {signal.source}"
    )

    print(
        f"URL: {signal.source_url}"
    )