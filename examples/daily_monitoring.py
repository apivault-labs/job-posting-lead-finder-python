"""
Daily monitoring loop with cross-run dedup.

Schedule daily (cron / GitHub Actions / Windows Task Scheduler). Only
charges for **newly listed** jobs by deduplicating against the previous
run's company+title+city fingerprint set. Keeps your CRM fresh
without re-paying for unchanged listings.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/daily_monitoring.py
"""

from __future__ import annotations

import json
from pathlib import Path

from job_lead_finder import JobLeadFinderClient


WATCHED_KEYWORDS = "marketing manager"
WATCHED_LOCATION = "United States"
STATE_FILE = Path("job_monitor_state.json")


def main() -> None:
    client = JobLeadFinderClient()

    previous: list[dict] = []
    if STATE_FILE.exists():
        previous = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    today, summary = client.search(
        keywords=WATCHED_KEYWORDS,
        location=WATCHED_LOCATION,
        deduplicate_companies=False,
        only_fresh_this_week=True,    # focus on fresh
    )

    new_listings = client.deduplicate_across_runs(previous, today)
    print(f"Today: {len(today)} total, "
          f"{len(new_listings)} new since last run")

    # The fresh hot leads
    fresh_hot = client.filter_by_lead_tier(new_listings,
                                              "scorching", "hot")
    if fresh_hot:
        print(f"\n=== {len(fresh_hot)} fresh hot+ leads ===")
        for j in fresh_hot[:10]:
            salary = j.get("salaryMedianUsd")
            sal = f"${salary:,.0f}" if salary else "n/a"
            print(f"  [{j.get('leadScore', 0):3}] "
                  f"{j.get('companyName', '?'):30}  "
                  f"{j.get('jobTitle', '')[:40]}  ({sal})")

    # Persist all of today's records so tomorrow's run can dedup
    STATE_FILE.write_text(
        json.dumps(today, ensure_ascii=False),
        encoding="utf-8",
    )

    if summary:
        print(f"\nFresh today across all leads: "
              f"{summary.get('fresh_today_count', 0)}")


if __name__ == "__main__":
    main()
