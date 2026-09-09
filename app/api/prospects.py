from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.discovery import (
    DiscoveryCandidate,
)

from app.models.lead import (
    CompanyInput,
    CompanySignal,
)

from app.services.company_enrichment import (
    enrich_candidate,
)

from app.agents.scout import (
    scout_company,
)

from app.services.outreach import (
    build_outreach_brief,
)

from app.services.outreach_generator import (
    build_outreach_messages,
)

from app.services.contact_researcher import (
    research_contacts,
)


router = APIRouter(
    prefix="/api/prospects",
    tags=["Prospect Intelligence"],
)


# ============================================================
# REQUEST MODELS
# ============================================================


class ProspectSignalRequest(BaseModel):

    signal_type: str

    title: str

    description: str | None = None

    source: str | None = None

    source_url: str | None = None

    source_trust: int = Field(
        default=40,
        ge=0,
        le=100,
    )

    strength: int = Field(
        default=50,
        ge=0,
        le=100,
    )

    officially_verified: bool = False

    verification_level: str = (
        "NOT_VERIFIED"
    )

    official_careers_found: bool = False

    exact_job_verified: bool = False

    careers_url: str | None = None


class ProspectAnalyzeRequest(BaseModel):

    company_name: str = Field(
        min_length=2
    )

    website: str | None = None

    country: str | None = None

    industry: str | None = None

    employee_count: int | None = None

    description: str | None = None

    signal: ProspectSignalRequest


# ============================================================
# SERIALIZATION
# ============================================================


def serialize_value(
    value: Any,
):

    if hasattr(
        value,
        "model_dump",
    ):

        return value.model_dump()

    if isinstance(
        value,
        list,
    ):

        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):

        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):

        return {
            key: serialize_value(item)
            for key, item in value.items()
        }

    return value


# ============================================================
# PROSPECT INTELLIGENCE
# ============================================================


@router.post(
    "/analyze"
)
def analyze_prospect(
    request: ProspectAnalyzeRequest,
):

    print()
    print(
        "============================================================"
    )
    print(
        "[API] PROSPECT INTELLIGENCE"
    )
    print(
        "============================================================"
    )

    print(
        f"[API] Company: "
        f"{request.company_name}"
    )

    print(
        f"[API] Website: "
        f"{request.website}"
    )

    print(
        f"[API] Signal: "
        f"{request.signal.signal_type}"
    )

    try:

        # ====================================================
        # 1. BUILD COMPANY SIGNAL
        # ====================================================

        company_signal = CompanySignal(

            signal_type=(
                request.signal.signal_type
            ),

            description=(
                request.signal.description
                or request.signal.title
            ),

            discovery_source="API",

            source=(
                request.signal.source
            ),

            source_url=(
                request.signal.source_url
            ),

            source_trust=(
                request.signal.source_trust
            ),

            strength=(
                request.signal.strength
            ),

            officially_verified=(
                request.signal.officially_verified
            ),

            verification_level=(
                request.signal.verification_level
            ),

            official_careers_found=(
                request.signal.official_careers_found
            ),

            exact_job_verified=(
                request.signal.exact_job_verified
            ),

            careers_url=(
                request.signal.careers_url
            ),
        )

        print(
            "[API] Company signal created"
        )

        # ====================================================
        # 2. BUILD COMPANY INPUT
        # ====================================================

        company = CompanyInput(

            company_name=(
                request.company_name
            ),

            website=(
                request.website
            ),

            country=(
                request.country
            ),

            industry=(
                request.industry
            ),

            employee_count=(
                request.employee_count
            ),

            description=(
                request.description
            ),

            signals=[
                company_signal
            ],
        )

        print(
            "[API] Company input created"
        )

        # ====================================================
        # 3. COMPANY ENRICHMENT
        # ====================================================

        print()
        print(
            "[API] Enriching company"
        )

        try:

            # ------------------------------------------------
            # IMPORTANT:
            #
            # company_enrichment.enrich_candidate()
            # expects a DiscoveryCandidate.
            #
            # CompanyInput is a different model and does not
            # contain confidence/discovery_source.
            #
            # Therefore we explicitly convert CompanyInput
            # into DiscoveryCandidate before enrichment.
            # ------------------------------------------------

            discovery_candidate = DiscoveryCandidate(

                company_name=(
                    company.company_name
                ),

                website=(
                    company.website
                ),

                country=(
                    company.country
                ),

                industry=(
                    company.industry
                ),

                employee_count=(
                    company.employee_count
                ),

                description=(
                    company.description
                ),

                discovery_source="API",

                source_url=(
                    company_signal.source_url
                ),

                confidence=80,
            )

            print(
                "[API] Discovery candidate created "
                "for enrichment"
            )

            # ------------------------------------------------
            # Run enrichment
            # ------------------------------------------------

            enriched = enrich_candidate(
                discovery_candidate
            )

            # ------------------------------------------------
            # Copy enriched values back into CompanyInput
            # ------------------------------------------------

            if enriched:

                if getattr(
                    enriched,
                    "website",
                    None,
                ):

                    company.website = (
                        enriched.website
                    )

                if getattr(
                    enriched,
                    "country",
                    None,
                ):

                    company.country = (
                        enriched.country
                    )

                if getattr(
                    enriched,
                    "industry",
                    None,
                ):

                    company.industry = (
                        enriched.industry
                    )

                if getattr(
                    enriched,
                    "employee_count",
                    None,
                ) is not None:

                    company.employee_count = (
                        enriched.employee_count
                    )

                if getattr(
                    enriched,
                    "description",
                    None,
                ):

                    company.description = (
                        enriched.description
                    )

                print(
                    "[API] Company enrichment completed"
                )

                print(
                    f"[API] Enrichment confidence: "
                    f"{getattr(enriched, 'confidence', 'N/A')}"
                )

        except Exception as exc:

            print(
                "[API] Enrichment warning: "
                f"{exc}"
            )

        # ====================================================
        # 4. SCOUT AGENT
        # ====================================================

        print()
        print(
            "[API] Running Scout Agent"
        )

        scout_result = scout_company(
            company
        )

        print(
            "[API] Scout Agent completed"
        )

        print(
            f"[API] Priority: "
            f"{scout_result.priority}"
        )

        print(
            f"[API] Opportunity: "
            f"{scout_result.opportunity_score}/100"
        )

        print(
            f"[API] Service: "
            f"{scout_result.recommended_service}"
        )

        # ====================================================
        # 5. CONTACT RESEARCH
        # ====================================================

        print()
        print(
            "[API] Researching decision makers"
        )

        contacts = research_contacts(

            company_name=(
                company.company_name
            ),

            website=(
                company.website
            ),
        )

        print(
            "[API] Contact research completed"
        )

        # ====================================================
        # 6. BUILD OUTREACH BRIEF
        # ====================================================

        print()
        print(
            "[API] Building outreach brief"
        )

        outreach_brief = (
            build_outreach_brief(
                company=company,
                result=scout_result,
            )
        )

        print(
            "[API] Outreach brief created"
        )

        # ====================================================
        # 7. GENERATE OUTREACH MESSAGES
        # ====================================================

        print()
        print(
            "[API] Generating outreach messages"
        )

        outreach_messages = (
            build_outreach_messages(
                brief=outreach_brief
            )
        )

        print(
            "[API] Outreach messages created"
        )

        # ====================================================
        # 8. EVIDENCE
        # ====================================================

        evidence = {

            "signal": {

                "source": (
                    company_signal.source
                ),

                "source_url": (
                    company_signal.source_url
                ),

                "source_trust": (
                    company_signal.source_trust
                ),

                "strength": (
                    company_signal.strength
                ),

                "officially_verified": (
                    company_signal.officially_verified
                ),

                "verification_level": (
                    company_signal.verification_level
                ),

                "official_careers_found": (
                    company_signal
                    .official_careers_found
                ),

                "exact_job_verified": (
                    company_signal
                    .exact_job_verified
                ),

                "careers_url": (
                    company_signal.careers_url
                ),
            },

            "scout": {

                "icp_score": (
                    scout_result.icp_score
                ),

                "intent_score": (
                    scout_result.intent_score
                ),

                "evidence_quality": (
                    scout_result.evidence_quality
                ),

                "opportunity_score": (
                    scout_result.opportunity_score
                ),

                "reasoning": (
                    scout_result.reasoning
                ),
            },

            "outreach": {

                "trigger_evidence": (
                    outreach_brief
                    .trigger_evidence
                ),

                "evidence_gaps": (
                    outreach_brief
                    .evidence_gaps
                ),
            },
        }

        # ====================================================
        # 9. DASHBOARD RESPONSE
        # ====================================================

        response = {

            "success": True,

            "company": serialize_value(
                company
            ),

            "signal": serialize_value(
                company_signal
            ),

            "scout": serialize_value(
                scout_result
            ),

            "contacts": serialize_value(
                contacts
            ),

            "outreach": {

                "brief": serialize_value(
                    outreach_brief
                ),

                "messages": serialize_value(
                    outreach_messages
                ),
            },

            "evidence": evidence,
        }

        print()
        print(
            "[API] Prospect intelligence completed"
        )

        print(
            f"[API] Contact status: "
            f"{contacts.contact_status}"
        )

        print(
            f"[API] Best contact: "
            f"{contacts.best_contact}"
        )

        print(
            "============================================================"
        )

        return response

    except Exception as exc:

        print()
        print(
            "[API] Prospect intelligence failed:"
        )

        print(
            str(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )