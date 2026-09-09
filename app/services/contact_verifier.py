import re

from app.models.contact import DecisionMaker


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"www\.", "", value)
    value = re.sub(r"[^a-z0-9\s@._-]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# PERSON DETECTION
# ============================================================

BLOCKED_PHRASES = [
    "about us",
    "developer roadmap",
    "roadmap",
    "issue #",
    "github",
    "engineering manager roadmap",
    "documentation",
    "blog",
    "careers",
    "jobs",
    "contact",
    "team",
    "home",
]


def is_probable_person(
    name: str | None,
) -> bool:

    if not name:
        return False

    name = name.strip()

    if len(name) < 4:
        return False

    lower = name.lower()

    for phrase in BLOCKED_PHRASES:
        if phrase in lower:
            return False

    words = name.split()

    if len(words) < 2 or len(words) > 5:
        return False

    if any(ch.isdigit() for ch in name):
        return False

    return True


# ============================================================
# ROLE MATCH
# ============================================================

def role_match_score(
    target: str,
    discovered: str | None,
) -> int:

    if not discovered:
        return 0

    target = _normalize(target)
    discovered = _normalize(discovered)

    if target == discovered:
        return 100

    if "cto" in target and (
        "cto" in discovered
        or "chief technology officer" in discovered
    ):
        return 100

    if (
        "vp engineering" in target
        and "engineering" in discovered
        and "vp" in discovered
    ):
        return 95

    if (
        "head of engineering" in target
        and "head of engineering" in discovered
    ):
        return 100

    if (
        "director of engineering" in target
        and "director of engineering" in discovered
    ):
        return 95

    if (
        "engineering manager" in target
        and "engineering manager" in discovered
    ):
        return 100

    return 0


# ============================================================
# COMPETING COMPANY DETECTION
# ============================================================

def _known_competing_company(
    company_name: str,
    title: str | None,
    description: str | None,
) -> str | None:

    """
    Detect a genuine competing-company association.

    IMPORTANT:
    Do NOT treat every phrase after a dash as another
    company. Search engines frequently return titles such as:

        Person - Executive Bio
        Person - Profile
        Person - Article

    Those are not necessarily employers.

    We only reject when the evidence clearly associates
    the person with another organization.
    """

    target = _normalize(company_name)

    title_text = _normalize(title)
    description_text = _normalize(
        description
    )

    combined = (
        f"{title_text} {description_text}"
    )

    # Known examples of search-result noise.
    noise_phrases = [
        "executive bio",
        "executive biography",
        "profile",
        "bio",
        "about",
        "article",
        "news",
        "interview",
        "podcast",
        "webinar",
        "conference",
        "speaker",
        "author",
        "issue",
        "roadmap",
        "job",
        "jobs",
        "careers",
    ]

    # If the text after a dash is merely a generic
    # content/page descriptor, don't treat it as a company.
    for phrase in noise_phrases:

        if phrase in combined:
            return None

    # --------------------------------------------------------
    # Strong company indicators
    # --------------------------------------------------------

    company_patterns = [
        r"\bat\s+([a-z0-9][a-z0-9 .&'-]{1,80})",
        r"\bwith\s+([a-z0-9][a-z0-9 .&'-]{1,80})",
        r"\bof\s+([a-z0-9][a-z0-9 .&'-]{1,80})",
        r"\bfrom\s+([a-z0-9][a-z0-9 .&'-]{1,80})",
    ]

    for pattern in company_patterns:

        matches = re.findall(
            pattern,
            combined,
        )

        for match in matches:

            candidate = match.strip(
                " .,-"
            )

            if not candidate:
                continue

            normalized = _normalize(
                candidate
            )

            if not normalized:
                continue

            if target in normalized:
                continue

            # Ignore obvious generic words.
            generic = {
                "linkedin",
                "search",
                "profile",
                "executive bio",
                "bio",
                "article",
                "website",
                "company",
                "team",
            }

            if normalized in generic:
                continue

            return candidate

    return None


# ============================================================
# COMPANY VERIFICATION
# ============================================================

def verify_company_association(
    company_name: str,
    person_name: str | None,
    role: str | None,
    title: str | None,
    description: str | None,
    linkedin_url: str | None,
):

    company = _normalize(
        company_name
    )

    combined = " ".join(
        [
            _normalize(title),
            _normalize(description),
            _normalize(linkedin_url),
        ]
    )

    # --------------------------------------------------------
    # Target company must appear in evidence
    # --------------------------------------------------------

    if company not in combined:

        return (
            False,
            0,
            "Target company not found in search evidence.",
        )

    # --------------------------------------------------------
    # Reject strong competing-company evidence
    # --------------------------------------------------------

    competing_company = (
        _known_competing_company(
            company_name=company_name,
            title=title,
            description=description,
        )
    )

    if competing_company:

        return (
            False,
            0,
            (
                "Search result identifies another "
                f"company ({competing_company}) "
                "for this person."
            ),
        )

    # --------------------------------------------------------
    # Person name must be supported
    # --------------------------------------------------------

    if person_name:

        person = _normalize(
            person_name
        )

        if (
            person
            and person not in combined
        ):

            return (
                False,
                0,
                "Person name not supported by search evidence.",
            )

    # --------------------------------------------------------
    # Role must be supported
    # --------------------------------------------------------

    if role:

        role_text = _normalize(
            role
        )

        if role_text == "cto":

            role_found = (
                "cto" in combined
                or "chief technology officer"
                in combined
            )

        else:

            role_found = (
                role_text in combined
            )

        if not role_found:

            return (
                False,
                0,
                "Role not supported by search evidence.",
            )

    # --------------------------------------------------------
    # Association confidence
    # --------------------------------------------------------

    score = 70

    if linkedin_url:
        score += 20

    if person_name:
        score += 10

    return (
        True,
        min(score, 100),
        (
            "Person, company and role "
            "verified from search evidence."
        ),
    )


# ============================================================
# CONTACT CONFIDENCE
# ============================================================

def verify_contact(
    contact: DecisionMaker,
) -> DecisionMaker:

    contact.linkedin_status = (
        "LIKELY"
        if contact.linkedin_url
        else "NOT_FOUND"
    )

    contact.email_status = (
        "UNVERIFIED"
        if contact.email
        else "NOT_FOUND"
    )

    confidence = int(
        contact.role_match * 0.35
    )

    if contact.linkedin_url:
        confidence += 25

    if contact.email:
        confidence += 20

    confidence += min(
        len(contact.evidence) * 5,
        20,
    )

    contact.contact_confidence = min(
        confidence,
        100,
    )

    return contact


# ============================================================
# BEST CONTACT
# ============================================================

def select_best_contact(
    contacts: list[DecisionMaker],
):

    if not contacts:
        return None

    contacts = [
        verify_contact(contact)
        for contact in contacts
    ]

    # --------------------------------------------------------
    # Important:
    #
    # A discovered person with incomplete information is
    # still a useful prospect.
    #
    # Therefore the minimum threshold is 40 rather than 60.
    #
    # We will use contact_status to distinguish PARTIAL
    # from FOUND.
    # --------------------------------------------------------

    contacts = [
        contact
        for contact in contacts
        if contact.contact_confidence >= 40
    ]

    if not contacts:
        return None

    contacts.sort(
        key=lambda contact: (
            contact.contact_confidence,
            bool(contact.linkedin_url),
            bool(contact.email),
            contact.role_match,
        ),
        reverse=True,
    )

    return contacts[0]