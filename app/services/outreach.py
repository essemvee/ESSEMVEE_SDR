from app.models.lead import (
    CompanyInput,
    CompanySignal,
    ScoutResult,
)
from app.models.outreach import (
    OutreachBrief,
)


def build_outreach_brief(
    company: CompanyInput,
    result: ScoutResult,
) -> OutreachBrief:
    """
    Convert ScoutResult and company evidence into a
    structured sales-ready OutreachBrief.

    This function does not invent facts.

    It separates:

    - What the evidence actually establishes
    - What remains unknown
    - The verified trigger
    - The appropriate ESSEMVEE angle
    - The recommended next sales action
    """

    signals = company.signals

    # --------------------------------------------------
    # Trigger
    # --------------------------------------------------

    hiring_signals = [
        signal
        for signal in signals
        if signal.signal_type.lower() == "hiring"
    ]

    if hiring_signals:

        primary_signal = hiring_signals[0]

        trigger = primary_signal.description

        trigger_evidence = []

        if primary_signal.source:
            trigger_evidence.append(
                f"External source: "
                f"{primary_signal.source}"
            )

        if primary_signal.source_url:
            trigger_evidence.append(
                f"Evidence URL: "
                f"{primary_signal.source_url}"
            )

        verification_level = getattr(
            primary_signal,
            "verification_level",
            "NOT_VERIFIED",
        )

        if verification_level == (
            "EXACT_JOB_VERIFIED"
        ):
            trigger_evidence.append(
                "Official company website "
                "independently exposes the exact job."
            )

        elif verification_level == (
            "CAREERS_CONFIRMED"
        ):
            trigger_evidence.append(
                "Official company careers page "
                "was confirmed, but the exact job "
                "was not exposed in retrieved "
                "static HTML."
            )

        elif verification_level == (
            "EXTERNAL_ONLY"
        ):
            trigger_evidence.append(
                "Hiring signal is supported by an "
                "external source only."
            )

        else:
            trigger_evidence.append(
                "Official verification was not "
                "established."
            )

    else:

        trigger = (
            "No specific current hiring trigger "
            "was established."
        )

        trigger_evidence = []

    # --------------------------------------------------
    # What we know
    # --------------------------------------------------

    what_we_know: list[str] = []

    if company.company_name:
        what_we_know.append(
            f"Company: {company.company_name}"
        )

    if company.country:
        what_we_know.append(
            f"Market: {company.country}"
        )

    if company.industry:
        what_we_know.append(
            f"Industry: {company.industry}"
        )

    if company.employee_count is not None:
        what_we_know.append(
            f"Employee count: "
            f"{company.employee_count}"
        )

    if company.description:
        what_we_know.append(
            f"Company description: "
            f"{company.description}"
        )

    for signal in signals:

        description = (
            signal.description.strip()
        )

        if description:
            what_we_know.append(
                description
            )

    # --------------------------------------------------
    # Evidence gaps
    # --------------------------------------------------

    evidence_gaps: list[str] = []

    if hiring_signals:

        hiring_signal = hiring_signals[0]

        verification_level = getattr(
            hiring_signal,
            "verification_level",
            "NOT_VERIFIED",
        )

        exact_job_verified = getattr(
            hiring_signal,
            "exact_job_verified",
            False,
        )

        if not exact_job_verified:

            if verification_level == (
                "CAREERS_CONFIRMED"
            ):
                evidence_gaps.append(
                    "The official careers page was "
                    "confirmed, but the exact vacancy "
                    "was not exposed in retrieved "
                    "static HTML."
                )

            else:
                evidence_gaps.append(
                    "The exact hiring signal has not "
                    "been independently verified on "
                    "the official company website."
                )

    evidence_gaps.extend(
        [
            "Specific technical pain point is not "
            "established by the available evidence.",
            "Current cloud platform or technology "
            "stack is not established.",
            "Budget or procurement intent is not "
            "established.",
            "External consulting or delivery-partner "
            "intent is not established.",
        ]
    )

    # --------------------------------------------------
    # Decision maker
    # --------------------------------------------------

    decision_maker_role = (
        result.decision_maker_role
    )

    # --------------------------------------------------
    # ESSEMVEE angle
    # --------------------------------------------------

    if (
        result.recommended_service
        == "DevOps"
    ):

        essemvee_angle = (
            "Position ESSEMVEE as an Ireland-based "
            "DevOps delivery partner that can provide "
            "additional engineering capacity while "
            "the company builds or expands its "
            "internal DevOps capability. Do not "
            "assume a specific cloud platform, "
            "tooling, or technical problem until "
            "validated."
        )

    elif (
        result.recommended_service
        == "Cloud Engineering"
    ):

        essemvee_angle = (
            "Position ESSEMVEE around cloud engineering "
            "delivery and additional technical "
            "capacity, while validating the company's "
            "actual cloud environment and priorities "
            "before proposing a specific solution."
        )

    elif (
        result.recommended_service
        == "DevSecOps"
    ):

        essemvee_angle = (
            "Position ESSEMVEE around secure software "
            "delivery, DevSecOps automation, and "
            "engineering enablement, without assuming "
            "a specific security gap that has not "
            "been evidenced."
        )

    elif (
        result.recommended_service
        == "AI & MLOps"
    ):

        essemvee_angle = (
            "Position ESSEMVEE around AI/MLOps "
            "engineering capability and platform "
            "delivery, while validating the company's "
            "actual AI infrastructure requirements."
        )

    else:

        essemvee_angle = (
            "Lead with ESSEMVEE's technology "
            "consulting capability and use the first "
            "conversation to validate the company's "
            "current engineering priorities."
        )

    # --------------------------------------------------
    # Recommended action
    # --------------------------------------------------

    recommended_action = (
        result.recommended_action
    )

    # --------------------------------------------------
    # Outreach strategy
    # --------------------------------------------------

    if hiring_signals:

        outreach_strategy = (
            "Use the hiring signal as the reason for "
            "contact. Reference the relevant role "
            "without claiming that the role has been "
            "officially confirmed unless the evidence "
            "level is EXACT_JOB_VERIFIED. Position "
            "ESSEMVEE as a potential source of interim "
            "or additional DevOps delivery capability. "
            "Ask an exploratory question about whether "
            "the team needs additional capacity while "
            "the role is being filled."
        )

    else:

        outreach_strategy = (
            "Use the strongest available evidence as "
            "the conversation trigger. Keep the first "
            "message exploratory and validate the "
            "company's current technology priorities "
            "before proposing a specific service."
        )

    return OutreachBrief(
        company_name=company.company_name,

        priority=result.priority,

        recommended_service=(
            result.recommended_service
        ),

        trigger=trigger,

        trigger_evidence=trigger_evidence,

        what_we_know=what_we_know,

        evidence_gaps=evidence_gaps,

        decision_maker_role=(
            decision_maker_role
        ),

        essemvee_angle=essemvee_angle,

        recommended_action=(
            recommended_action
        ),

        outreach_strategy=(
            outreach_strategy
        ),
    )