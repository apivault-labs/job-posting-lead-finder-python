"""
Full B2B sales outreach pipeline.

Filters job listings down to **scorching/hot leadTier** companies
with 3 ready-to-paste outreach pitch variants per company. Drop the
consultative variant into your first email, the aggressive into
follow-up #2, the referral into LinkedIn DM.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/sales_outreach_pipeline.py
"""

from job_lead_finder import JobLeadFinderClient


def main() -> None:
    client = JobLeadFinderClient()

    # 1. Server-side filters: hot leads with disclosed salary in US
    jobs, _ = client.search(
        keywords="head of marketing",
        location="United States",
        deduplicate_companies=False,    # keep multi-role data
        min_lead_score=55,              # hot+ tier only
        only_with_salary=True,
        top_n=30,
    )
    print(f"Server-side filtered: {len(jobs)} hot+ leads")

    # 2. Client-side narrowing — pull only decision-maker roles
    decision_makers = client.filter_by_seniority(
        jobs, "director", "vp", "c-level"
    )
    print(f"Decision-maker roles: {len(decision_makers)}")

    # 3. Pull TOP_HIRING_COMPANIES digest with 3 outreach variants each
    top = client.get_top_hiring_companies()
    if not top:
        print("No TOP_HIRING_COMPANIES digest available")
        return

    print(f"\n=== TOP {len(top['top_companies'])} HIRING COMPANIES ===\n")
    for c in top["top_companies"]:
        print(f"\n{c['companyName']}  ({c['jobs_count']} roles, "
              f"max_leadScore={c['max_leadScore']})")
        if c.get("avg_salary_usd"):
            print(f"  Avg salary: ${c['avg_salary_usd']:,.0f}")
        print(f"  Categories: {c.get('categories')}")
        print(f"  Sources active: {c.get('sources_active')}")
        print(f"  Top skills:  "
              f"{[s['name'] for s in (c.get('top_skills') or [])][:5]}")

        variants = c.get("outreachPitchVariants") or {}
        if variants:
            print(f"\n  ▼ CONSULTATIVE (cold email #1):")
            print(f"    {variants.get('consultative', '')}")
            print(f"\n  ▼ AGGRESSIVE (follow-up #2):")
            print(f"    {variants.get('aggressive', '')}")
            print(f"\n  ▼ REFERRAL (LinkedIn DM):")
            print(f"    {variants.get('referral', '')}")

        links = c.get("outreachLinks") or {}
        if links.get("linkedin_role_owner_search_url"):
            print(f"\n  Find the decision maker: "
                  f"{links['linkedin_role_owner_search_url']}")
        if links.get("email_template_url_with_pitch"):
            print(f"  Open mailto with pitch pre-filled: "
                  f"{links['email_template_url_with_pitch'][:120]}...")


if __name__ == "__main__":
    main()
