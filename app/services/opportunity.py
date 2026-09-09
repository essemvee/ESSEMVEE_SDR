from typing import Literal


Priority = Literal[
    "HOT",
    "WARM",
    "WATCH",
    "IGNORE",
]


def calculate_opportunity_score(
    icp_score: int,
    intent_score: int,
    evidence_quality: int,
) -> int:
    """
    Calculate the overall ESSEMVEE opportunity score.

    ICP Fit       = 40%
    Intent        = 40%
    Evidence      = 20%

    Returns a score from 0 to 100.
    """

    score = (
        icp_score * 0.40
        + intent_score * 0.40
        + evidence_quality * 0.20
    )

    return round(
        min(score, 100)
    )


def determine_priority(
    opportunity_score: int,
) -> Priority:

    if opportunity_score >= 80:
        return "HOT"

    if opportunity_score >= 60:
        return "WARM"

    if opportunity_score >= 40:
        return "WATCH"

    return "IGNORE"