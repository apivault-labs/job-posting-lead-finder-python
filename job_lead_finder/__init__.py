"""
Job Posting Lead Finder — Python SDK

Official Python client for the apivault_labs/apify-actor-job-leads
Apify actor (v1.2). Multi-source job aggregator (Indeed + LinkedIn,
optional Glassdoor) turned into a B2B sales prospecting tool.
$0.003 per job — 40+ enrichment fields per record.

Returns per job:

- Core: jobTitle, companyName, location, jobType, description,
  postedDate, companyRating, jobUrl, source, sources_seen[]
- Salary parser (USD-normalized): salaryMinUsd, salaryMaxUsd,
  salaryMedianUsd, salary_tier (entry/mid/senior/principal/unicorn),
  salaryPeriod, salaryCurrency — 7 currencies (USD/EUR/GBP/CAD/AUD/INR/JPY)
- Job freshness: daysSincePosted, freshness_tier (today/this_week/
  this_month/older)
- Work-mode classifier: workMode (remote/hybrid/onsite/unknown) +
  workMode_signals[]
- Skills extraction: skillsRequired[] (225 tech terms — Python, React,
  Postgres, AWS, Salesforce, HubSpot, Shopify, Snowflake, ...),
  softSkills[] (15), certifications[] (18), skillsCount
- Benefits parser: 14 boolean flags (mentions_401k, mentions_equity,
  mentions_visa_sponsorship, mentions_unlimited_pto, mentions_signing_bonus,
  ...) + benefitsCount
- Seniority normalizer: intern → c-level (seniority_normalized)
- Job category auto-detect: 15 categories — engineering / data_science /
  product / design / sales / marketing / finance / hr / operations /
  legal / customer_support / healthcare / education / construction_trades /
  other
- Location parser: parsedLocation: {city, state, country}, isUsListing,
  isRemoteListing
- DEI signals: 7 boolean flags (mentions_diversity, mentions_lgbtq,
  mentions_women, mentions_veteran_friendly, mentions_disability_friendly,
  mentions_eeo, mentions_pay_transparency) + dei_signals_count
- US pay transparency law detection: pay_transparency_state (CA / CO /
  CT / MD / NV / NY / RI / WA / DC / IL / MN / MA),
  pay_transparency_law, pay_transparency_compliant
- **leadScore (0-100)** + leadTier (cold/warm/hot/scorching) +
  leadScoreReasons[] — composite of cross-source presence × hiring
  volume × freshness × salary disclosure × seniority × benefits ×
  visa sponsorship × employer rating

Free aggregate KV records on bulk runs:
- **SUMMARY** — total_jobs, by_source, by_lead_tier, by_seniority,
  by_category, by_work_mode, by_freshness, top_companies,
  top_skills_demanded, salary distribution (median + p25 + p75),
  remote_friendly_pct, fresh_today_count
- **TOP_HIRING_COMPANIES** — top 20 sorted by job count, with
  sources_active[], max_leadScore, categories, top_skills, avg_salary_usd,
  outreachPitch + **3 outreach pitch variants** (consultative /
  aggressive / referral) + outreachLinks (LinkedIn company / hiring
  manager / role-owner search by category / Google careers / mailto
  with auto-pasted pitch)
- **TOP_JOBS** — top 20 jobs sorted by leadScore (sales-ops digest)

Multi-format export: ``default`` (full JSON, 40+ fields) /
``csv`` (flat 35-column row ready for HubSpot / Pipedrive / Salesforce)

Quick start:

    from job_lead_finder import JobLeadFinderClient

    client = JobLeadFinderClient(api_token="apify_api_xxxxxx")

    jobs, summary = client.search(
        keywords="marketing manager",
        location="New York, NY",
        min_lead_score=55,
        only_with_salary=True,
    )

    # Hottest sales prospects
    for j in client.filter_by_lead_tier(jobs, "scorching", "hot"):
        print(f"{j['companyName']:30}  lead={j['leadScore']:3}  "
              f"{j.get('salary_tier'):10}  {j['jobTitle']}")

    # Daily TOP_HIRING_COMPANIES digest with 3 ready-to-paste pitches
    top = client.get_top_hiring_companies()
    for c in (top or {}).get("top_companies", [])[:10]:
        print(c["companyName"], c["jobs_count"], "roles")
        print("  ", c["outreachPitchVariants"]["consultative"])

See https://github.com/apivault-labs/job-posting-lead-finder-python
for full docs.
"""

from .client import JobLeadFinderClient
from .exceptions import (
    ActorRunError,
    ActorTimeoutError,
    AuthenticationError,
    JobLeadFinderError,
)

__version__ = "0.1.0"
__all__ = [
    "JobLeadFinderClient",
    "JobLeadFinderError",
    "AuthenticationError",
    "ActorRunError",
    "ActorTimeoutError",
]
