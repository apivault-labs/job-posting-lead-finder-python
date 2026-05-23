"""
Tech-stack targeted outreach.

If you sell Salesforce add-ons, find companies hiring Salesforce admins.
If you sell DevOps tooling, find companies hiring "DevOps engineer with
Kubernetes". The actor returns ``skillsRequired[]`` per job — filter
client-side, then build outreach by category.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/tech_skills_targeted_outreach.py
"""

from collections import Counter

from job_lead_finder import JobLeadFinderClient


# Customize: skills that signal "this company would buy our product"
TARGET_SKILLS = ["Kubernetes", "Terraform"]
ROLE_KEYWORDS = "devops engineer"


def main() -> None:
    client = JobLeadFinderClient()

    jobs, summary = client.search(
        keywords=ROLE_KEYWORDS,
        location="United States",
        deduplicate_companies=False,    # multi-role per company
        min_lead_score=20,
    )
    print(f"Total: {len(jobs)} jobs")

    # match_all=False → match any of the listed skills (broader funnel)
    matching = client.filter_by_skills(jobs, *TARGET_SKILLS,
                                          match_all=False)
    print(f"Match any of {TARGET_SKILLS}: {len(matching)}")

    matching_strict = client.filter_by_skills(jobs, *TARGET_SKILLS,
                                                 match_all=True)
    print(f"Match ALL of {TARGET_SKILLS}: {len(matching_strict)}")

    # Top companies hiring this stack
    by_company = Counter(j.get("companyName") for j in matching
                         if j.get("companyName"))
    print(f"\nTop companies hiring {' + '.join(TARGET_SKILLS)}:")
    for company, count in by_company.most_common(10):
        print(f"  {count:3} role(s)  {company}")

    # Top demanded skills overall (use SUMMARY)
    if summary and summary.get("top_skills_demanded"):
        print("\nTop 10 skills demanded across all jobs:")
        for s in summary["top_skills_demanded"][:10]:
            print(f"  {s['count']:3}× {s['name']}")


if __name__ == "__main__":
    main()
