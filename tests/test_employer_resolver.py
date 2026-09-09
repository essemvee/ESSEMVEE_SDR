from app.services.employer_resolver import (
    EmployerResolver,
)


resolver = EmployerResolver()


companies = [
    "Deciphex",
    "Beyond Inc",
]


print()
print("==============================")
print("ESSEMVEE EMPLOYER RESOLVER")
print("==============================")
print()


for company in companies:

    website = resolver.resolve(
        company
    )

    print(
        f"Company: {company}"
    )

    print(
        f"Website: {website}"
    )

    print()