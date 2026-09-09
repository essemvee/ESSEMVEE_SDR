import os

from dotenv import load_dotenv
from openai import OpenAI

from app.models.lead import (
    CompanyInput,
    ScoutResult,
)
from app.services.evidence import (
    calculate_evidence_quality,
)
from app.services.opportunity import (
    calculate_opportunity_score,
    determine_priority,
)
from app.services.scoring import (
    calculate_icp_score,
)


load_dotenv()


def get_openai_client() -> OpenAI:

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing from .env"
        )

    return OpenAI(
        api_key=api_key
    )


SCOUT_INSTRUCTIONS = """
You are the ESSEMVEE Scout Agent.

ESSEMVEE Technology Services is an
Ireland-based technology consulting company.

Core services:

1. Cloud Engineering
2. DevOps
3. DevSecOps
4. AI & MLOps
5. Data & Analytics

Target customers include:

- SaaS companies
- software companies
- technology companies
- startups
- scale-ups
- SMEs
- fintech
- healthtech
- AI companies
- digital businesses
- IT consultancies

Analyze the supplied company information
and signals.

Your responsibility is to determine:

1. Intent score from 0-100.
2. Most relevant ESSEMVEE service.
3. Likely technical/business problem.
4. Why ESSEMVEE should approach now.
5. Appropriate decision-maker role.
6. Recommended next sales action.
7. Evidence-based reasoning.

IMPORTANT:

Do NOT invent information.

Use only the supplied company information
and signals.

Do not invent:

- funding
- projects
- budgets
- technologies
- employees
- customers
- people
- contracts
- pain points

If the evidence does not establish a
specific problem, explicitly say so.

Intent score guidance:

90-100:
Very strong current buying signal.

75-89:
Strong evidence of a relevant current need.

60-74:
Moderate evidence.

40-59:
Weak or indirect evidence.

0-39:
Little or no evidence of current intent.

Hiring for DevOps, Cloud, Kubernetes,
Terraform, platform engineering, AI,
MLOps or similar technical roles can be
strong intent signals.

A generic company profile without a current
signal should receive low intent.

Return a structured result.
"""


def scout_company(
    company: CompanyInput,
) -> ScoutResult:

    client = get_openai_client()

    # -----------------------------------------
    # Deterministic scoring
    # -----------------------------------------

    icp_score = calculate_icp_score(
        company
    )

    evidence_quality = (
        calculate_evidence_quality(
            company.signals
        )
    )

    # -----------------------------------------
    # AI analysis
    # -----------------------------------------

    response = client.responses.parse(
        model=os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6-luna",
        ),
        instructions=SCOUT_INSTRUCTIONS,
        input=company.model_dump_json(),
        text_format=ScoutResult,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "Scout Agent returned no result."
        )

    # -----------------------------------------
    # Our scoring engine owns these values
    # -----------------------------------------

    result.icp_score = icp_score

    result.evidence_quality = (
        evidence_quality
    )

    result.opportunity_score = (
        calculate_opportunity_score(
            icp_score=icp_score,
            intent_score=result.intent_score,
            evidence_quality=evidence_quality,
        )
    )

    result.priority = determine_priority(
        result.opportunity_score
    )

    return result