from app.models.lead import CompanyInput, CompanySignal
from app.services.scoring import calculate_icp_score


company = CompanyInput(
    company_name="Example SaaS",
    website="https://example.com",
    country="Ireland",
    industry="B2B SaaS",
    employee_count=120,
    description="B2B SaaS company expanding its engineering team.",
    signals=[
        CompanySignal(
            signal_type="Hiring",
            description="Hiring Senior DevOps Engineer",
            source="Careers page",
            strength=90,
        ),
        CompanySignal(
            signal_type="Cloud",
            description="Looking for Azure experience",
            source="Job description",
            strength=90,
        ),
    ],
)


score = calculate_icp_score(company)

print(f"Company: {company.company_name}")
print(f"ICP Score: {score}/100")