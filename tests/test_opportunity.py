from app.services.opportunity import (
    calculate_opportunity_score,
    determine_priority,
)


icp_score = 75
intent_score = 90
evidence_quality = 96


opportunity_score = calculate_opportunity_score(
    icp_score,
    intent_score,
    evidence_quality,
)


priority = determine_priority(
    opportunity_score
)


print()
print("==============================")
print("ESSEMVEE OPPORTUNITY")
print("==============================")
print()
print(f"ICP Score: {icp_score}/100")
print(f"Intent Score: {intent_score}/100")
print(
    f"Evidence Quality: "
    f"{evidence_quality}/100"
)
print(
    f"Opportunity Score: "
    f"{opportunity_score}/100"
)
print(f"Priority: {priority}")
print()