from app.agents.scout import scout_company
from app.models.lead import (
    CompanyInput,
    CompanySignal,
)


company = CompanyInput(
    company_name="Example SaaS",
    website="https://example.com",
    country="Ireland",
    industry="B2B SaaS",
    employee_count=120,
    description=(
        "A growing B2B SaaS company serving "
        "European businesses."
    ),
    signals=[
        CompanySignal(
            signal_type="Hiring",
            description=(
                "The company is hiring a "
                "Senior DevOps Engineer."
            ),
            source="Company careers page",
            strength=90,
        ),
        CompanySignal(
            signal_type="Cloud",
            description=(
                "A current engineering role "
                "requires Azure experience."
            ),
            source="Job description",
            strength=90,
        ),
        CompanySignal(
            signal_type="Engineering Growth",
            description=(
                "The company is expanding "
                "its engineering team."
            ),
            source="Company careers page",
            strength=80,
        ),
    ],
)


result = scout_company(company)


print()
print("========================================")
print("       ESSEMVEE SCOUT RESULT")
print("========================================")
print()
print(f"Company: {result.company_name}")
print(f"ICP Score: {result.icp_score}/100")
print(f"Intent Score: {result.intent_score}/100")
print(
    f"Evidence Quality: "
    f"{result.evidence_quality}/100"
)
print(
    f"Opportunity Score: "
    f"{result.opportunity_score}/100"
)
print(f"Priority: {result.priority}")
print(f"Priority: {result.priority}")
print(f"Service: {result.recommended_service}")
print(f"Problem: {result.likely_problem}")
print(f"Why Now: {result.why_now}")
print(f"Decision Maker: {result.decision_maker_role}")
print(f"Action: {result.recommended_action}")
print()
print("Reasoning:")

for reason in result.reasoning:
    print(f"- {reason}")

print()
print("========================================")