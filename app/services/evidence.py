from app.models.lead import CompanySignal


VERIFICATION_BOOSTS = {
    "EXACT_JOB_VERIFIED": 15,
    "CAREERS_CONFIRMED": 8,
    "EXTERNAL_ONLY": 0,
    "NOT_VERIFIED": 0,
}


def calculate_verification_boost(
    signal: CompanySignal,
) -> int:
    """
    Calculate the evidence-quality adjustment based on
    independent verification.

    Verification levels:

    EXACT_JOB_VERIFIED
        The official company website independently exposes
        the exact job represented by the signal.

    CAREERS_CONFIRMED
        The official company careers/open-roles page exists
        and is confirmed, but the exact job was not exposed
        in the retrieved static HTML.

    EXTERNAL_ONLY
        The signal is supported by an external source, but
        the company's official website did not independently
        confirm the signal.

    NOT_VERIFIED
        No meaningful verification was established.
    """

    verification_level = getattr(
        signal,
        "verification_level",
        "NOT_VERIFIED",
    )

    return VERIFICATION_BOOSTS.get(
        verification_level,
        0,
    )


def calculate_signal_evidence_quality(
    signal: CompanySignal,
) -> int:
    """
    Calculate evidence quality for a single signal.

    Base evidence quality is based on:

    - Source trust: 60%
    - Signal strength: 40%

    Verification then provides an additional adjustment.

    Verification is deliberately separated from
    source trust because a trustworthy third-party
    source and independent official confirmation
    represent different forms of evidence.
    """

    source_trust = max(
        0,
        min(
            signal.source_trust,
            100,
        ),
    )

    strength = max(
        0,
        min(
            signal.strength,
            100,
        ),
    )

    score = (
        source_trust * 0.60
        + strength * 0.40
    )

    verification_boost = (
        calculate_verification_boost(
            signal
        )
    )

    score += verification_boost

    return round(
        min(
            score,
            100,
        )
    )


def calculate_evidence_quality(
    signals: list[CompanySignal],
) -> int:
    """
    Calculate overall evidence quality.

    Multiple signals are averaged so that one weak
    source does not completely dominate the result.

    Returns 0-100.
    """

    if not signals:
        return 0

    scores = []

    for signal in signals:

        score = (
            calculate_signal_evidence_quality(
                signal
            )
        )

        scores.append(
            score
        )

    average_score = (
        sum(scores)
        / len(scores)
    )

    return round(
        min(
            average_score,
            100,
        )
    )