from app.services.search_config import (
    ESSEMVEE_SEARCH_QUERIES,
    TARGET_COUNTRIES,
    TARGET_SERVICE_KEYWORDS,
)


print()
print("==============================")
print("ESSEMVEE SEARCH CONFIG")
print("==============================")
print()

print("Target countries:")

for country in TARGET_COUNTRIES:
    print(f"- {country}")

print()
print("Target service keywords:")

for keyword in TARGET_SERVICE_KEYWORDS:
    print(f"- {keyword}")

print()
print("Discovery queries:")

for query in ESSEMVEE_SEARCH_QUERIES:
    print(f"- {query}")