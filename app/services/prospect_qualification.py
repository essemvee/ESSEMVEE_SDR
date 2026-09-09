from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


# ============================================================
# ESSEMVEE PROSPECT QUALIFICATION
# ============================================================
#
# Purpose:
#
#   CRO / Registry
#        ↓
#   Active company validation
#        ↓
#   NACE / company-type qualification
#        ↓
#   ESSEMVEE ICP classification
#        ↓
#   Research / Reject
#
# IMPORTANT:
#
# A company does NOT need a website to qualify.
#
# New companies may have:
#
#   CRO record
#   +
#   relevant business activity
#   +
#   founder/director
#
# without having a website yet.
#
# This module performs deterministic qualification.
# It does NOT perform web research.
# It does NOT send email.
# It does NOT invent company information.
# ============================================================


# ============================================================
# QUALIFICATION LEVELS
# ============================================================

QUALIFIED = "QUALIFIED"
POSSIBLE = "POSSIBLE"
REJECT = "REJECT"


# ============================================================
# ESSEMVEE-RELEVANT NACE CODES
# ============================================================
#
# These are intentionally broad starting categories.
#
# We will refine this list after observing real CRO data.
#
# 62xx = computer programming / IT
# 63xx = information services
# 58xx = software / publishing
# 72xx = scientific research
# 70xx = management / consulting
# 71xx = engineering / technical services
#
# We do NOT automatically assume that every company
# in these categories is a sales opportunity.
#
# They are simply candidates for further research.
# ============================================================

RELEVANT_NACE_PREFIXES = (
    "58",
    "62",
    "63",
    "70",
    "71",
    "72",
)


# ============================================================
# STRONG TECHNOLOGY NACE PREFIXES
# ============================================================

STRONG_TECH_NACE_PREFIXES = (
    "62",
    "63",
)


# ============================================================
# COMPANY TYPES WE GENERALLY WANT
# ============================================================

PREFERRED_COMPANY_TYPE_TERMS = (
    "private company",
    "private limited",
    "ltd",
    "limited by shares",
)


# ============================================================
# COMPANY TYPES WE GENERALLY DO NOT WANT
# ============================================================

EXCLUDED_COMPANY_TYPE_TERMS = (
    "company limited by guarantee",
    "charitable",
    "charity",
)


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass
class QualificationResult:

    company_name: str

    qualification: str

    score: int

    active: bool

    new_company: bool

    relevant_nace: bool

    strong_technology_signal: bool

    website_required: bool

    research_founders: bool

    research_website: bool

    research_contacts: bool

    reasons: list[str]

    next_action: str


# ============================================================
# QUALIFIER
# ============================================================

class ProspectQualifier:

    """
    Deterministic ESSEMVEE prospect qualification engine.

    This class intentionally does not use AI.

    Its responsibility is to determine whether a company
    deserves additional research before entering the
    Scout / intelligence pipeline.
    """

    def __init__(
        self,
        recent_days: int = 90,
    ) -> None:

        if recent_days < 1:

            raise ValueError(
                "recent_days must be greater than zero."
            )

        self.recent_days = recent_days

    # ========================================================
    # PUBLIC QUALIFICATION METHOD
    # ========================================================

    def qualify(
        self,
        company: Any,
    ) -> QualificationResult:

        company_name = (
            self._get(
                company,
                "company_name",
            )
            or "Unknown company"
        )

        status = (
            self._get(
                company,
                "status",
            )
            or ""
        )

        company_type = (
            self._get(
                company,
                "company_type",
            )
            or ""
        )

        nace_code = (
            self._get(
                company,
                "nace_code",
            )
            or ""
        )

        registration_date = (
            self._get(
                company,
                "registration_date",
            )
        )

        # ----------------------------------------------------
        # Active status
        # ----------------------------------------------------

        active = self.is_active(
            company
        )

        # ----------------------------------------------------
        # New company
        # ----------------------------------------------------

        new_company = self.is_new_company(
            registration_date
        )

        # ----------------------------------------------------
        # NACE relevance
        # ----------------------------------------------------

        relevant_nace = (
            self.is_relevant_nace(
                nace_code
            )
        )

        strong_technology_signal = (
            self.is_strong_technology_nace(
                nace_code
            )
        )

        # ----------------------------------------------------
        # Score
        # ----------------------------------------------------

        score = 0

        reasons: list[str] = []

        # ----------------------------------------------------
        # Active company
        # ----------------------------------------------------

        if active:

            score += 40

            reasons.append(
                "Company appears to be active."
            )

        else:

            reasons.append(
                "Company does not appear to be active."
            )

        # ----------------------------------------------------
        # Relevant NACE
        # ----------------------------------------------------

        if relevant_nace:

            score += 30

            reasons.append(
                f"NACE {nace_code} is relevant "
                "to ESSEMVEE's target sectors."
            )

        else:

            reasons.append(
                f"NACE {nace_code or 'not established'} "
                "is not currently classified as an "
                "ESSEMVEE-relevant sector."
            )

        # ----------------------------------------------------
        # Strong technology signal
        # ----------------------------------------------------

        if strong_technology_signal:

            score += 15

            reasons.append(
                "Company has a strong technology/"
                "information-services NACE signal."
            )

        # ----------------------------------------------------
        # New company
        # ----------------------------------------------------

        if new_company:

            score += 10

            reasons.append(
                "Company is newly registered and "
                "should be considered for founder/"
                "director-led outreach."
            )

        # ----------------------------------------------------
        # Preferred company type
        # ----------------------------------------------------

        if self.is_preferred_company_type(
            company_type
        ):

            score += 5

            reasons.append(
                "Company type is suitable for "
                "commercial prospect research."
            )

        # ----------------------------------------------------
        # Excluded company type
        # ----------------------------------------------------

        if self.is_excluded_company_type(
            company_type
        ):

            score -= 40

            reasons.append(
                "Company type is generally excluded "
                "from the initial ESSEMVEE prospecting "
                "pipeline."
            )

        # ----------------------------------------------------
        # Clamp score
        # ----------------------------------------------------

        score = max(
            0,
            min(
                100,
                score,
            ),
        )

        # ----------------------------------------------------
        # Qualification
        # ----------------------------------------------------

        if not active:

            qualification = REJECT

            next_action = (
                "Archive as historical/inactive company."
            )

        elif strong_technology_signal and score >= 70:

            qualification = QUALIFIED

            next_action = (
                "Research founder/director, website "
                "if available, LinkedIn and verified "
                "contact sources."
            )

        elif relevant_nace and score >= 60:

            qualification = POSSIBLE

            next_action = (
                "Perform additional company and "
                "decision-maker research before "
                "sending to Scout."
            )

        else:

            qualification = REJECT

            next_action = (
                "Do not send to the active SDR pipeline."
            )

        # ----------------------------------------------------
        # Research strategy
        # ----------------------------------------------------

        # Website is NEVER mandatory for a new company.

        website_required = False

        research_founders = (
            qualification in {
                QUALIFIED,
                POSSIBLE,
            }
        )

        research_website = (
            qualification in {
                QUALIFIED,
                POSSIBLE,
            }
        )

        research_contacts = (
            qualification == QUALIFIED
        )

        # ----------------------------------------------------
        # Special handling for new companies
        # ----------------------------------------------------

        if (
            new_company
            and active
            and relevant_nace
        ):

            research_founders = True

            reasons.append(
                "Because the company is new, "
                "founder/director research should "
                "be performed even if no website "
                "exists."
            )

        return QualificationResult(

            company_name=company_name,

            qualification=qualification,

            score=score,

            active=active,

            new_company=new_company,

            relevant_nace=relevant_nace,

            strong_technology_signal=(
                strong_technology_signal
            ),

            website_required=website_required,

            research_founders=(
                research_founders
            ),

            research_website=(
                research_website
            ),

            research_contacts=(
                research_contacts
            ),

            reasons=reasons,

            next_action=next_action,
        )

    # ========================================================
    # ACTIVE STATUS
    # ========================================================

    @staticmethod
    def is_active(
        company: Any,
    ) -> bool:

        # Prefer the CRO object's existing property
        # when available.

        try:

            value = getattr(
                company,
                "is_active",
            )

            if callable(value):

                value = value()

            if isinstance(
                value,
                bool,
            ):

                return value

        except Exception:

            pass

        status = str(
            ProspectQualifier._get(
                company,
                "status",
            )
            or ""
        ).strip().lower()

        if not status:

            return False

        inactive_terms = (
            "dissolved",
            "struck off",
            "liquidation",
            "liquidated",
            "receivership",
            "cancelled",
            "ceased",
        )

        return not any(
            term in status
            for term in inactive_terms
        )

    # ========================================================
    # NEW COMPANY
    # ========================================================

    def is_new_company(
        self,
        registration_date: Any,
    ) -> bool:

        parsed = self._parse_date(
            registration_date
        )

        if parsed is None:

            return False

        today = date.today()

        cutoff = (
            today
            - self._days_to_delta(
                self.recent_days
            )
        )

        return (
            cutoff
            <= parsed
            <= today
        )

    # ========================================================
    # NACE
    # ========================================================

    @staticmethod
    def is_relevant_nace(
        nace_code: Any,
    ) -> bool:

        code = (
            str(
                nace_code or ""
            )
            .strip()
            .replace(
                ".",
                "",
            )
        )

        if not code:

            return False

        return code.startswith(
            RELEVANT_NACE_PREFIXES
        )

    # ========================================================
    # STRONG TECHNOLOGY NACE
    # ========================================================

    @staticmethod
    def is_strong_technology_nace(
        nace_code: Any,
    ) -> bool:

        code = (
            str(
                nace_code or ""
            )
            .strip()
            .replace(
                ".",
                "",
            )
        )

        if not code:

            return False

        return code.startswith(
            STRONG_TECH_NACE_PREFIXES
        )

    # ========================================================
    # COMPANY TYPE
    # ========================================================

    @staticmethod
    def is_preferred_company_type(
        company_type: Any,
    ) -> bool:

        text = str(
            company_type or ""
        ).strip().lower()

        if not text:

            return False

        return any(
            term in text
            for term in PREFERRED_COMPANY_TYPE_TERMS
        )

    # ========================================================
    # EXCLUDED COMPANY TYPE
    # ========================================================

    @staticmethod
    def is_excluded_company_type(
        company_type: Any,
    ) -> bool:

        text = str(
            company_type or ""
        ).strip().lower()

        if not text:

            return False

        return any(
            term in text
            for term in EXCLUDED_COMPANY_TYPE_TERMS
        )

    # ========================================================
    # DATE PARSER
    # ========================================================

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> date | None:

        if value is None:

            return None

        if isinstance(
            value,
            datetime,
        ):

            return value.date()

        if isinstance(
            value,
            date,
        ):

            return value

        text = str(
            value
        ).strip()

        if not text:

            return None

        # ISO datetime

        try:

            return datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            ).date()

        except ValueError:

            pass

        # Common formats

        for fmt in (
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ):

            try:

                return datetime.strptime(
                    text,
                    fmt,
                ).date()

            except ValueError:

                continue

        return None

    # ========================================================
    # DAYS → TIMEDELTA
    # ========================================================

    @staticmethod
    def _days_to_delta(
        days: int,
    ):
        from datetime import timedelta

        return timedelta(
            days=days
        )

    # ========================================================
    # GENERIC GETTER
    # ========================================================

    @staticmethod
    def _get(
        obj: Any,
        field: str,
    ) -> Any:

        if isinstance(
            obj,
            dict,
        ):

            return obj.get(
                field
            )

        return getattr(
            obj,
            field,
            None,
        )


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def qualify_prospect(
    company: Any,
    recent_days: int = 90,
) -> QualificationResult:

    qualifier = ProspectQualifier(
        recent_days=recent_days
    )

    return qualifier.qualify(
        company
    )


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    print()

    print(
        "============================================================"
    )

    print(
        "       ESSEMVEE — PROSPECT QUALIFICATION TEST"
    )

    print(
        "============================================================"
    )

    # --------------------------------------------------------
    # Test records based on the CRO structure.
    # --------------------------------------------------------

    test_companies = [

        {
            "company_name": (
                "IOBOXX AGENTIC OS LIMITED"
            ),
            "status": "Normal",
            "company_type": (
                "LTD - Private Company Limited by Shares"
            ),
            "registration_date": (
                "2026-07-30"
            ),
            "nace_code": "6201",
        },

        {
            "company_name": (
                "TASTY KEBAB HOUSE LIMITED"
            ),
            "status": "Normal",
            "company_type": (
                "LTD - Private Company Limited by Shares"
            ),
            "registration_date": (
                "2026-07-30"
            ),
            "nace_code": "5610",
        },

        {
            "company_name": (
                "ABANDONED HISTORICAL COMPANY LIMITED"
            ),
            "status": "Dissolved",
            "company_type": (
                "Private limited by shares"
            ),
            "registration_date": (
                "1998-01-01"
            ),
            "nace_code": "6201",
        },
    ]

    qualifier = ProspectQualifier(
        recent_days=90
    )

    for company in test_companies:

        result = qualifier.qualify(
            company
        )

        print()

        print(
            "------------------------------------------------------------"
        )

        print(
            f"Company: "
            f"{result.company_name}"
        )

        print(
            f"Qualification: "
            f"{result.qualification}"
        )

        print(
            f"Score: "
            f"{result.score}/100"
        )

        print(
            f"Active: "
            f"{result.active}"
        )

        print(
            f"New company: "
            f"{result.new_company}"
        )

        print(
            f"Relevant NACE: "
            f"{result.relevant_nace}"
        )

        print(
            f"Strong technology signal: "
            f"{result.strong_technology_signal}"
        )

        print(
            f"Website required: "
            f"{result.website_required}"
        )

        print(
            f"Research founders/directors: "
            f"{result.research_founders}"
        )

        print(
            f"Research website: "
            f"{result.research_website}"
        )

        print(
            f"Research contacts: "
            f"{result.research_contacts}"
        )

        print()

        print(
            "Reasons:"
        )

        for reason in result.reasons:

            print(
                f"- {reason}"
            )

        print()

        print(
            f"Next action: "
            f"{result.next_action}"
        )

    print()

    print(
        "============================================================"
    )

    print(
        "Qualification test completed."
    )

    print(
        "============================================================"
    )