"""
Quickstart: run a job search and print the hottest sales prospects.

    pip install -r requirements.txt
    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/quickstart.py
"""

from job_lead_finder import JobLeadFinderClient


def main() -> None:
    client = JobLeadFinderClient()  # picks up APIFY_API_TOKEN from env

    jobs, summary = client.search(
        keywords="marketing manager",
        location="New York, NY",
        sources=("indeed", "linkedin"),
    )

    print(f"\nTotal: {len(jobs)} jobs")
    if summary:
        print(f"  Sources:        {summary.get('by_source', {})}")
        print(f"  Lead tiers:     {summary.get('by_lead_tier', {})}")
        print(f"  Salary median:  "
              f"${summary.get('salary_median_usd', 0):,.0f}")
        print(f"  Remote-friendly: {summary.get('remote_friendly_pct', 0)}%")
        print(f"  Fresh today:    {summary.get('fresh_today_count', 0)}")

    print("\n=== Top 5 prospects (by leadScore) ===")
    top5 = sorted(jobs,
                  key=lambda j: -(j.get("leadScore") or 0))[:5]
    for j in top5:
        salary = j.get("salaryMedianUsd")
        salary_str = f"${salary:,.0f}" if salary else "n/a"
        print(f"\n{j.get('companyName')} — {j.get('jobTitle', '')[:60]}")
        print(f"  leadScore: {j.get('leadScore', 0)} "
              f"({j.get('leadTier', '?')})")
        print(f"  salary:    {salary_str} ({j.get('salary_tier', '?')})")
        print(f"  posted:    {j.get('freshness_tier', '?')}, "
              f"workMode: {j.get('workMode', '?')}")
        print(f"  sources:   {j.get('sources_seen') or [j.get('source')]}")
        for r in (j.get("leadScoreReasons") or [])[:3]:
            print(f"    + {r}")


if __name__ == "__main__":
    main()
