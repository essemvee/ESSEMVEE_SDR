from app.models.signal import (
    CompanySignals,
    Signal,
)


def normalize_signal(
    signal: Signal,
) -> Signal:

    signal.title = signal.title.strip()

    signal.description = (
        signal.description.strip()
    )

    signal.source = (
        signal.source.strip()
    )

    if signal.source_url:
        signal.source_url = (
            signal.source_url.strip()
        )

    return signal


def normalize_signals(
    company_name: str,
    signals: list[Signal],
) -> CompanySignals:

    normalized = []

    seen = set()

    for signal in signals:

        signal = normalize_signal(
            signal
        )

        # Avoid duplicate signals
        key = (
            signal.signal_type,
            signal.title.lower(),
            signal.source_url,
        )

        if key in seen:
            continue

        seen.add(key)

        normalized.append(signal)

    return CompanySignals(
        company_name=company_name,
        signals=normalized,
    )