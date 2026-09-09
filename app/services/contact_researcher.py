from app.models.contact import (
    ContactEvidence,
    DecisionMaker,
)

from app.services.contact_intelligence import (
    build_contact_intelligence,
)

from app.services.contact_verifier import (
    role_match_score,
    verify_company_association,
)

from app.services.web_discovery import (
    WebDiscoverySource,
)


# ============================================================
# ROLE TARGETS
# ============================================================

DEFAULT_ROLES = [
    "CTO",
    "VP Engineering",
    "Head of Engineering",
    "Director of Engineering",
    "Engineering Manager",
]


# ============================================================
# HELPERS
# ============================================================

def _extract_linkedin_url(
    result: dict,
) -> str | None:

    url = result.get("url")

    if not url:
        return None

    if "linkedin.com/in/" in url.lower():
        return url

    return None


def _clean_name(
    value: str,
) -> str:

    value = value.strip()

    # Remove role suffix.
    role_markers = [
        " | CTO",
        " | VP Engineering",
        " | Head of Engineering",
        " | Director of Engineering",
        " | Engineering Manager",
    ]

    for marker in role_markers:

        if marker.lower() in value.lower():

            value = value.split(
                marker,
                1,
            )[0]

            break

    return value.strip()


def _extract_candidate_name(
    result: dict,
    company_name: str,
) -> str | None:

    title = (
        result.get("title")
        or ""
    ).strip()

    if not title:
        return None

    # --------------------------------------------------------
    # First remove the role suffix.
    #
    # Example:
    #
    # Saul Hodder - Automat-it | CTO
    #
    # becomes:
    #
    # Saul Hodder - Automat-it
    # --------------------------------------------------------

    cleaned = _clean_name(
        title
    )

    # --------------------------------------------------------
    # If there is a company suffix, remove it from the
    # person's name.
    #
    # Example:
    #
    # Liviu Dobrea - Deciphex
    #
    # becomes:
    #
    # Liviu Dobrea
    #
    # Saul Hodder - Automat-it
    #
    # becomes:
    #
    # Saul Hodder
    # --------------------------------------------------------

    if " - " in cleaned:

        person_part, company_part = (
            cleaned.split(
                " - ",
                1,
            )
        )

        company_part = (
            company_part.strip()
        )

        target_company = (
            company_name
            .strip()
            .lower()
        )

        # In both cases the left side is the person.
        #
        # The company part is deliberately not included
        # in the name.
        #
        # Company verification happens separately.
        if company_part:

            cleaned = person_part.strip()

    elif " – " in cleaned:

        person_part, company_part = (
            cleaned.split(
                " – ",
                1,
            )
        )

        if company_part.strip():

            cleaned = person_part.strip()

    elif " — " in cleaned:

        person_part, company_part = (
            cleaned.split(
                " — ",
                1,
            )
        )

        if company_part.strip():

            cleaned = person_part.strip()

    # --------------------------------------------------------
    # Basic person validation
    # --------------------------------------------------------

    if not cleaned:
        return None

    blocked = [
        "about us",
        "developer roadmap",
        "roadmap",
        "issue #",
        "github",
        "careers",
        "jobs",
        "engineering manager roadmap",
        "executive bio",
        "executive biography",
        "profile",
    ]

    lower = cleaned.lower()

    for phrase in blocked:

        if phrase in lower:

            return None

    words = cleaned.split()

    if len(words) < 2:
        return None

    if len(words) > 5:
        return None

    if any(
        character.isdigit()
        for character in cleaned
    ):
        return None

    return cleaned


def _result_text(
    result: dict,
) -> str:

    return " ".join(
        [
            result.get(
                "title",
                "",
            ),
            result.get(
                "description",
                "",
            ),
            result.get(
                "url",
                "",
            ),
        ]
    )


def _extract_role(
    result: dict,
    target_role: str,
) -> str | None:

    text = _result_text(
        result
    ).lower()

    target = target_role.lower()

    if target == "cto":

        if (
            " cto" in f" {text}"
            or "chief technology officer"
            in text
        ):
            return "CTO"

    if target == "vp engineering":

        if (
            "vp engineering" in text
            or "vp of engineering" in text
            or "vice president engineering"
            in text
        ):
            return "VP Engineering"

    if target == "head of engineering":

        if (
            "head of engineering"
            in text
        ):
            return "Head of Engineering"

    if target == "director of engineering":

        if (
            "director of engineering"
            in text
        ):
            return "Director of Engineering"

    if target == "engineering manager":

        if (
            "engineering manager"
            in text
        ):
            return "Engineering Manager"

    return None


# ============================================================
# EXPLICIT COMPANY FROM TITLE
# ============================================================

def _extract_title_company(
    result: dict,
) -> str | None:

    title = (
        result.get("title")
        or ""
    ).strip()

    if not title:
        return None

    # Remove role suffix first.
    cleaned = _clean_name(
        title
    )

    for separator in [
        " - ",
        " – ",
        " — ",
    ]:

        if separator in cleaned:

            _, company = (
                cleaned.split(
                    separator,
                    1,
                )
            )

            company = company.strip()

            if company:

                return company

    return None


# ============================================================
# RESULT -> CONTACT
# ============================================================

def _build_contact_from_result(
    company_name: str,
    target_role: str,
    result: dict,
) -> DecisionMaker | None:

    title = (
        result.get(
            "title",
            "",
        )
    )

    description = (
        result.get(
            "description",
            "",
        )
    )

    # --------------------------------------------------------
    # Explicit employer/company from title
    # --------------------------------------------------------

    title_company = (
        _extract_title_company(
            result
        )
    )

    if title_company:

        target = (
            company_name
            .strip()
            .lower()
        )

        employer = (
            title_company
            .strip()
            .lower()
        )

        if (
            employer != target
            and target not in employer
            and employer not in target
        ):

            print(
                "[CONTACT] REJECT: "
                f"result explicitly associates "
                f"person with another company "
                f"({title_company})"
            )

            return None

    # --------------------------------------------------------
    # Extract person
    # --------------------------------------------------------

    name = _extract_candidate_name(
        result=result,
        company_name=company_name,
    )

    if not name:

        print(
            "[CONTACT] REJECT: "
            "not a person"
        )

        return None

    # --------------------------------------------------------
    # Extract role
    # --------------------------------------------------------

    role = _extract_role(
        result,
        target_role,
    )

    if not role:

        print(
            "[CONTACT] REJECT: "
            f"role not established "
            f"for {target_role}"
        )

        return None

    linkedin_url = (
        _extract_linkedin_url(
            result
        )
    )

    # --------------------------------------------------------
    # Company / role verification
    # --------------------------------------------------------

    (
        associated,
        association_score,
        reason,
    ) = verify_company_association(
        company_name=company_name,
        person_name=name,
        role=role,
        title=title,
        description=description,
        linkedin_url=linkedin_url,
    )

    if not associated:

        print(
            "[CONTACT] REJECT: "
            f"{reason}"
        )

        return None

    role_match = role_match_score(
        target_role,
        role,
    )

    evidence = [
        ContactEvidence(
            source="Brave Search",
            source_url=result.get(
                "url"
            ),
            evidence_type=(
                "company_role_association"
            ),
            description=(
                "Search evidence associates "
                f"{name} with "
                f"{company_name} and "
                f"the role {role}."
            ),
            confidence=association_score,
        )
    ]

    source_urls = []

    if result.get("url"):

        source_urls.append(
            result["url"]
        )

    if linkedin_url:

        evidence.append(
            ContactEvidence(
                source="LinkedIn",
                source_url=linkedin_url,
                evidence_type=(
                    "linkedin_profile"
                ),
                description=(
                    "A LinkedIn profile URL "
                    "was found in the search "
                    "evidence."
                ),
                confidence=60,
            )
        )

        source_urls.append(
            linkedin_url
        )

    contact = DecisionMaker(
        company_name=company_name,
        name=name,
        role=role,
        role_match=role_match,
        linkedin_url=linkedin_url,
        email=None,
        evidence=evidence,
        source_urls=list(
            dict.fromkeys(
                source_urls
            )
        ),
        notes=[
            reason,
        ],
    )

    print(
        "[CONTACT] VERIFIED SCORE: "
        f"{name} | {role} | "
        f"{association_score}/100"
    )

    print(
        "[CONTACT] ACCEPTED: "
        f"{name} | {role} | "
        f"{association_score}/100"
    )

    return contact


# ============================================================
# WEB SEARCH
# ============================================================

def _search_role(
    source: WebDiscoverySource,
    company_name: str,
    target_role: str,
) -> list[DecisionMaker]:

    query = (
        f'"{company_name}" '
        f'"{target_role}"'
    )

    print()

    print(
        f"[CONTACT] Searching: "
        f"{query}"
    )

    results = source.search(
        query=query,
        count=5,
    )

    print(
        f"[CONTACT] Results: "
        f"{len(results)}"
    )

    contacts = []

    for result in results:

        contact = (
            _build_contact_from_result(
                company_name=company_name,
                target_role=target_role,
                result=result,
            )
        )

        if contact:

            contacts.append(
                contact
            )

    return contacts


# ============================================================
# LINKEDIN SEARCH
# ============================================================

def _search_linkedin_role(
    source: WebDiscoverySource,
    company_name: str,
    target_role: str,
) -> list[DecisionMaker]:

    query = (
        f'"{company_name}" '
        f'"{target_role}" '
        f"site:linkedin.com/in"
    )

    print()

    print(
        f"[CONTACT] LinkedIn search: "
        f"{query}"
    )

    results = source.search(
        query=query,
        count=5,
    )

    print(
        f"[CONTACT] Results: "
        f"{len(results)}"
    )

    contacts = []

    for result in results:

        linkedin_url = (
            _extract_linkedin_url(
                result
            )
        )

        if not linkedin_url:

            print(
                "[CONTACT] REJECT: "
                "not a LinkedIn profile"
            )

            continue

        contact = (
            _build_contact_from_result(
                company_name=company_name,
                target_role=target_role,
                result=result,
            )
        )

        if contact:

            contacts.append(
                contact
            )

    return contacts


# ============================================================
# MAIN
# ============================================================

def research_contacts(
    company_name: str,
    website: str | None = None,
    recommended_role: str = (
        "CTO, VP/Head of Engineering, "
        "or Engineering Manager"
    ),
):

    print()

    print(
        f"[CONTACT] Researching decision makers "
        f"for {company_name}"
    )

    if website:

        print(
            f"[CONTACT] Company website: "
            f"{website}"
        )

    source = WebDiscoverySource()

    contacts = []

    for target_role in DEFAULT_ROLES:

        contacts.extend(
            _search_role(
                source=source,
                company_name=company_name,
                target_role=target_role,
            )
        )

    for target_role in DEFAULT_ROLES:

        contacts.extend(
            _search_linkedin_role(
                source=source,
                company_name=company_name,
                target_role=target_role,
            )
        )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    unique = {}

    for contact in contacts:

        if contact.linkedin_url:

            key = (
                contact.linkedin_url
                .strip()
                .lower()
            )

        else:

            key = (
                f"{contact.name.strip().lower()}|"
                f"{contact.role.strip().lower()}"
            )

        existing = unique.get(
            key
        )

        if existing is None:

            unique[key] = contact

        elif (
            contact.contact_confidence
            > existing.contact_confidence
        ):

            unique[key] = contact

    contacts = list(
        unique.values()
    )

    print()

    print(
        f"[CONTACT] Contacts found: "
        f"{len(contacts)}"
    )

    intelligence = (
        build_contact_intelligence(
            company_name=company_name,
            recommended_role=recommended_role,
            contacts=contacts,
        )
    )

    print(
        f"[CONTACT] Status: "
        f"{intelligence.contact_status}"
    )

    if intelligence.best_contact:

        print(
            "[CONTACT] Best contact: "
            f"{intelligence.best_contact.name} "
            f"| "
            f"{intelligence.best_contact.role} "
            f"| "
            f"{intelligence.best_contact.contact_confidence}/100"
        )

    else:

        print(
            "[CONTACT] Best contact: NONE"
        )

    return intelligence