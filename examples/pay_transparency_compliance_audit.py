"""
HR-tech / legal-tech use case — pay-transparency law compliance audit.

12 US states have pay-transparency laws (CA, CO, CT, MD, NV, NY, RI,
WA, DC, IL, MN, MA). Companies hiring there MUST disclose salary
ranges. This script flags potential non-compliant listings — useful
for HR consultancies, legal-tech vendors, and compliance dashboards.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/pay_transparency_compliance_audit.py
"""

from collections import Counter

from job_lead_finder import JobLeadFinderClient


# Run state-by-state for a clean audit trail
TARGET_STATES = [
    ("California", "CA"),
    ("New York", "NY"),
    ("Colorado", "CO"),
    ("Washington", "WA"),
]


def main() -> None:
    client = JobLeadFinderClient()

    audit = []
    for state_name, state_code in TARGET_STATES:
        print(f"\n=== Auditing {state_name} ({state_code}) ===")
        jobs, _ = client.search(
            keywords="manager",        # broad — most listings
            location=state_name,
            deduplicate_companies=False,
            top_n=50,
        )

        # Listings actually located in the target state (location parser
        # provides parsedLocation.state)
        in_state = client.filter_by_state(jobs, state_code)
        if not in_state:
            print("  No in-state listings found.")
            continue

        # Compliance check
        compliant = client.filter_with_pay_transparency(in_state)
        non_compliant = [
            j for j in in_state
            if j.get("pay_transparency_state") == state_code
            and not j.get("pay_transparency_compliant")
        ]

        print(f"  Total in-state:     {len(in_state)}")
        print(f"  Compliant:          {len(compliant)}")
        print(f"  Non-compliant:      {len(non_compliant)}")

        if non_compliant:
            print(f"\n  Sample non-compliant (no salary disclosed):")
            for j in non_compliant[:5]:
                print(f"    {j.get('companyName')}  "
                      f"{j.get('jobTitle', '')[:50]}")

        # Track for cross-state report
        for j in non_compliant:
            audit.append({
                "state": state_code,
                "company": j.get("companyName"),
                "jobTitle": j.get("jobTitle"),
                "url": j.get("jobUrl"),
            })

    # Cross-state summary — companies non-compliant in multiple states
    by_company = Counter(a["company"] for a in audit if a["company"])
    repeat_offenders = [
        c for c, count in by_company.most_common() if count >= 2
    ]
    if repeat_offenders:
        print(f"\n=== Repeat offenders ({len(repeat_offenders)}) ===")
        print("Companies non-compliant in 2+ states:")
        for c in repeat_offenders[:20]:
            print(f"  {c}  ({by_company[c]} states)")


if __name__ == "__main__":
    main()
