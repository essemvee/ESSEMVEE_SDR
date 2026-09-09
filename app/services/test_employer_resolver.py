from app.services.employer_resolver import EmployerResolver


def main():
    resolver = EmployerResolver()

    companies = [
        "House Surveys",
        "Thrive Investments",
        "Indexe IT",
        "Deciphex",
    ]

    print("=" * 80)
    print("ESSEMVEE EMPLOYER RESOLVER TEST")
    print("=" * 80)

    for company in companies:
        print()
        print(f"COMPANY: {company}")
        print("-" * 80)

        try:
            website = resolver.resolve(company)

            if website:
                print(f"RESULT: VERIFIED OFFICIAL WEBSITE")
                print(f"WEBSITE: {website}")
            else:
                print("RESULT: NO VERIFIED OFFICIAL WEBSITE")

        except Exception as exc:
            print("RESULT: ERROR")
            print(f"ERROR: {exc}")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()