"""
Cross-source winners — the strongest budget signal.

Companies that posted the *same* role on Indeed AND LinkedIn are
running multi-channel hiring campaigns. That means real budget,
real urgency, and a much higher chance your outreach lands.

The actor's cross-source dedup collapses these duplicates into a
single record with ``sources_seen=["indeed","linkedin"]`` — this
script extracts those.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/cross_source_winners.py
"""

from collections import Counter

from job_lead_finder import JobLeadFinderClient


def main() -> None:
    client = JobLeadFinderClient()

    jobs, summary = client.search(
        keywords="head of growth",
        location="United States",
        sources=("indeed", "linkedin"),
        deduplicate_companies=False,    # keep all roles
        top_n=30,
    )
    print(f"Total: {len(jobs)} jobs")

    # Cross-source winners — present on 2+ boards
    winners = client.filter_cross_source(jobs, min_sources=2)
    print(f"Cross-source winners (on Indeed AND LinkedIn): {len(winners)}")

    # Sort by leadScore — these are your hottest prospects
    winners.sort(key=lambda j: -(j.get("leadScore") or 0))

    print("\n=== Top cross-source prospects ===\n")
    for j in winners[:15]:
        print(f"  [{j.get('leadScore', 0):3}] "
              f"{j.get('leadTier', '?'):10} "
              f"{j.get('companyName', '?'):30}  "
              f"{j.get('jobTitle', '')[:50]}")
        print(f"        sources: {j.get('sources_seen')}, "
              f"category: {j.get('jobCategory')}, "
              f"seniority: {j.get('seniority_normalized')}")
        if j.get("salaryMedianUsd"):
            print(f"        salary: ${j['salaryMedianUsd']:,.0f} "
                  f"({j.get('salary_tier')})")
        print()

    # Aggregate: what types of roles do cross-source companies post?
    if winners:
        cats = Counter(j.get("jobCategory") for j in winners)
        print(f"\nCross-source role categories: {dict(cats)}")

        seniority = Counter(j.get("seniority_normalized") for j in winners)
        print(f"Cross-source seniority breakdown: {dict(seniority)}")


if __name__ == "__main__":
    main()
