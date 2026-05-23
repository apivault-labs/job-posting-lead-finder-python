"""
Bulk multi-keyword search and read the SUMMARY +
TOP_HIRING_COMPANIES + TOP_JOBS digest.

The aggregates are written for free to the run's KV store and
serve as your daily sales-ops digest.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/bulk_search.py
"""

from job_lead_finder import JobLeadFinderClient


KEYWORDS = [
    "marketing manager",
    "head of growth",
    "director of marketing",
]
LOCATION = "United States"


def main() -> None:
    client = JobLeadFinderClient()
    print(f"Estimated cost per query: "
          f"${client.estimate_cost(80):.4f}")

    all_jobs: list[dict] = []
    for kw in KEYWORDS:
        print(f"\n=== Searching: {kw!r} ===")
        jobs, summary = client.search(
            keywords=kw,
            location=LOCATION,
            deduplicate_companies=False,
            min_lead_score=30,
            top_n=20,
        )
        print(f"  {len(jobs)} jobs after server-side filters")
        if summary:
            print(f"  Lead tiers: {summary.get('by_lead_tier', {})}")

        # Free TOP_HIRING_COMPANIES digest with 3-variant pitches
        top = client.get_top_hiring_companies()
        if top and top.get("top_companies"):
            print(f"\n  Top 5 hiring companies for '{kw}':")
            for c in top["top_companies"][:5]:
                print(f"    {c['companyName']}  "
                      f"({c['jobs_count']} roles, "
                      f"max_leadScore={c['max_leadScore']})")
                if c.get("outreachPitchVariants"):
                    pitch = c["outreachPitchVariants"]["consultative"]
                    print(f"      pitch: {pitch[:120]}...")

        all_jobs.extend(jobs)

    print(f"\n=== Combined: {len(all_jobs)} jobs across "
          f"{len(KEYWORDS)} queries ===")

    # Cross-source winners — shows up on multiple boards
    cross = client.filter_cross_source(all_jobs, min_sources=2)
    print(f"\nCross-source hires (= active multi-channel hiring): "
          f"{len(cross)}")
    for j in cross[:5]:
        print(f"  {j['companyName']}  {j.get('jobTitle', '')[:50]}  "
              f"sources={j.get('sources_seen')}")


if __name__ == "__main__":
    main()
