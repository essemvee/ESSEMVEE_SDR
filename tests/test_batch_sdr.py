from app.services.batch_sdr import (
    run_batch_sdr,
    print_batch_results,
)


def main():

    query = (
        '"Senior DevOps Engineer" '
        '"Ireland" '
        '-LinkedIn '
        '-Indeed '
        '-Glassdoor '
        '-IrishJobs'
    )

    leads = run_batch_sdr(
        query=query,
        count=5,
        max_results=10,
    )

    print_batch_results(
        leads
    )


if __name__ == "__main__":
    main()