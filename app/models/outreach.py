from pydantic import BaseModel


class OutreachBrief(BaseModel):
    """
    Structured sales intelligence generated from
    verified company and signal evidence.
    """

    company_name: str

    priority: str

    recommended_service: str

    trigger: str

    trigger_evidence: list[str]

    what_we_know: list[str]

    evidence_gaps: list[str]

    decision_maker_role: str

    essemvee_angle: str

    recommended_action: str

    outreach_strategy: str