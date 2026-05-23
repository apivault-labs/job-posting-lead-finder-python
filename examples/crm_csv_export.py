"""
CRM-ready CSV export.

Set ``export_format="csv"`` to receive flat 35-column rows ready for
direct import into HubSpot / Pipedrive / Salesforce. Each row has
exactly the fields your CRM expects (companyName, jobTitle, location,
salaryMedianUsd, leadScore, leadTier, jobUrl, ...).

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/crm_csv_export.py
"""

from __future__ import annotations

import csv

from job_lead_finder import JobLeadFinderClient


def main() -> None:
    client = JobLeadFinderClient()

    rows, _ = client.search(
        keywords="sales director",
        location="United States",
        min_lead_score=40,
        only_with_salary=True,
        export_format="csv",          # ← key switch
        write_summary=False,
    )
    if not rows:
        print("No leads found.")
        return

    # Each row is already a flat dict with the CRM-friendly fields.
    fieldnames = [k for k in rows[0].keys() if not k.startswith("_")]
    with open("sales_leads.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames,
                                  extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} leads to sales_leads.csv "
          f"({len(fieldnames)} columns)")
    print("Now import at:")
    print("  HubSpot:    Contacts → Import → File from computer")
    print("  Pipedrive:  Tools → Import data → CSV / Excel")
    print("  Salesforce: Setup → Data Import Wizard → Custom Object")


if __name__ == "__main__":
    main()
