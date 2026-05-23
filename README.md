# 💼 Job Posting Lead Finder — Python SDK

[![PyPI version](https://img.shields.io/badge/pip-job--posting--lead--finder-blue.svg)](https://github.com/apivault-labs/job-posting-lead-finder-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/apivault-labs/job-posting-lead-finder-python/actions/workflows/ci.yml/badge.svg)](https://github.com/apivault-labs/job-posting-lead-finder-python/actions/workflows/ci.yml)

> **40+ enrichment fields per job. $0.003 each. CRM-ready output. 3
> outreach pitch variants per company. No login. No LinkedIn API
> required.**

Multi-source job aggregator (**Indeed + LinkedIn Jobs**, optional
Glassdoor) turned into a B2B sales prospecting tool. Companies that
are hiring have active budgets — making them the best prospects for
your outreach.

Direct alternative to **Apollo / ZoomInfo / RocketReach / LinkedIn
Sales Navigator** ($99-$300+/mo subscriptions): pay-as-you-go, real-
time hiring data, leadScore for prioritization, three ready-to-paste
outreach variants per company, and a flat CSV export ready for
HubSpot / Salesforce / Pipedrive.

```bash
pip install git+https://github.com/apivault-labs/job-posting-lead-finder-python
```

```python
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
```

## Why Job Postings = Best B2B Leads

| Signal | What It Tells You |
|--------|-------------------|
| Cross-board hiring (Indeed + LinkedIn) | Multi-channel investment = active budget |
| Multiple roles per company | Scaling fast |
| Disclosed salary range | Mature comp ops + budget transparency |
| Senior / VP / C-level role | Decision maker outreach window |
| Modern tech stack in description | Vendors & tools they need |
| Visa sponsorship | Global talent ops scaling |

A company posting 5+ jobs is spending $50K–$500K+ on new hires.
Combined with their tech stack signals you know **what they need
next** before they do.

## What you get for $0.003 per job

For every job analyzed you get **40+ structured fields** combining
core data with **12 derived enrichment layers**.

### ⭐ Core
- `jobTitle`, `companyName`, `location`, `jobType`
- `description`, `postedDate`, `companyRating`, `jobUrl`
- `source` (which board returned this row)
- `sources_seen[]` — boards this job appeared on after cross-source
  dedup (cross-board hiring = serious budget signal)

### 💰 Salary parser (USD-normalized)
- `salaryMinUsd`, `salaryMaxUsd`, `salaryMedianUsd`
- `salary_tier` — entry / mid / senior / principal / unicorn
- 7 currencies: USD/EUR/GBP/CAD/AUD/INR/JPY (FX-converted)
- Hourly/daily/weekly/monthly auto-annualized

### ⏱️ Job freshness
- `daysSincePosted`, `freshness_tier`
  (today / this_week / this_month / older)

### 🌍 Work-mode classifier
- `workMode` — remote / hybrid / onsite / unknown
- `isRemoteListing` boolean

### 🛠️ Skills extraction (225 tech terms)
- `skillsRequired[]` — Python, React, Postgres, AWS, Kubernetes,
  Salesforce, HubSpot, Shopify, Snowflake, Marketo, Pardot, ...
- `softSkills[]` (15 phrases), `certifications[]` (18 patterns),
  `skillsCount`

### 🎁 Benefits parser (14 boolean flags)
`mentions_401k`, `mentions_health_insurance`, `mentions_equity`,
`mentions_remote_work`, `mentions_visa_sponsorship`,
`mentions_relocation`, `mentions_unlimited_pto`,
`mentions_parental_leave`, `mentions_signing_bonus`,
`mentions_4_day_week`, `mentions_stipend`, `mentions_meals`,
`mentions_gym`, `mentions_commuter_benefits`, plus `benefitsCount`

### 🎯 Seniority normalizer (10 buckets)
intern → junior → mid → senior → lead → staff → principal →
director → vp → c-level. Reliable across noisy titles.

### 🏷️ Job category auto-detect (15 categories)
engineering / data_science / product / design / sales / marketing /
finance / hr / operations / legal / customer_support / healthcare /
education / construction_trades / other

### 🏠 Location parser
`parsedLocation: {city, state, country}`, `isUsListing`,
`isRemoteListing`. Strips US zip codes, parenthetical neighborhoods,
"Remote in / Hybrid in" prefixes.

### 🏛️ DEI signals (7 boolean flags)
`mentions_diversity`, `mentions_lgbtq`, `mentions_women`,
`mentions_veteran_friendly`, `mentions_disability_friendly`,
`mentions_eeo`, `mentions_pay_transparency`, plus `dei_signals_count`

### ⚖️ US pay-transparency law detection (12 states)
For listings in CA / CO / CT / MD / NV / NY / RI / WA / DC / IL / MN / MA:
- `pay_transparency_state`, `pay_transparency_law`
- `pay_transparency_compliant` — true if salary disclosed as required

### 🎯 **leadScore (0-100)** + tier + reasons

Composite for B2B sales prospecting:

- **Cross-board presence** — same job on Indeed AND LinkedIn = active
  multi-channel hiring (= real budget)
- **Hiring volume per company** (×5 roles = active budget)
- **Job freshness** — fresh = active demand
- **Salary disclosure** — mature comp practice
- **Modern tech stack** — well-funded engineering team
- **Benefits depth** — larger comp budget
- **Decision-maker seniority** — VP / director / c-level = budget owner
- **Visa sponsorship** — scaling talent ops
- **Employer rating** — high rating = healthy company

`leadTier` — cold / warm / hot / scorching
`leadScoreReasons[]` — explainable signals

### 💬 3 outreach pitch variants per company

Written to `TOP_HIRING_COMPANIES.outreachPitchVariants`:

- `consultative` — soft sell (default first email)
- `aggressive` — leads with a metric (follow-up #2)
- `referral` — mutual-connection angle (LinkedIn DM)

A/B test which copy converts in your sequence.

### 📞 One-click outreach links per company

- `linkedin_company_url`, `linkedin_jobs_at_company_url`
- `linkedin_hiring_manager_search_url`
- `linkedin_role_owner_search_url` — filtered by job category
  (engineering manager / cmo / cfo / head of design / ...)
- `google_search_url`, `careers_page_guess`
- `email_template_url_with_pitch` — mailto with auto-pasted pitch body

### 📊 Free aggregate KV records on bulk runs

**SUMMARY** — total jobs, by_source, by_category, by_seniority,
by_work_mode, by_freshness, by_lead_tier, top_companies,
top_skills_demanded, top_benefits_offered, salary distribution
(median + p25 + p75), remote_friendly_pct, fresh_today_count.

**TOP_HIRING_COMPANIES** — top 20 sorted by job count, with
`sources_active`, `max_leadScore`, `categories`, `top_skills`,
`avg_salary_usd`, **3 outreach pitch variants per company**,
full outreach links.

**TOP_JOBS** — top 20 jobs sorted by `leadScore` (sales-ops job-level
digest).

```python
top = client.get_top_hiring_companies()
for c in top["top_companies"][:5]:
    print(c["companyName"], c["jobs_count"], "roles")
    print("  Consultative:", c["outreachPitchVariants"]["consultative"])
    print("  Aggressive:  ", c["outreachPitchVariants"]["aggressive"])
    print("  Referral:    ", c["outreachPitchVariants"]["referral"])
```

## Sample output

```json
{
  "success": true,
  "source": "indeed",
  "sources_seen": ["indeed", "linkedin"],

  "jobTitle": "Senior Marketing Manager",
  "companyName": "Acme Corp",
  "location": "New York, NY",
  "parsedLocation": {"city": "New York", "state": "NY", "country": "US"},
  "isUsListing": true,
  "isRemoteListing": false,
  "workMode": "hybrid",

  "salaryMinUsd": 120000,
  "salaryMaxUsd": 150000,
  "salaryMedianUsd": 135000,
  "salary_tier": "senior",
  "salaryPeriod": "year",
  "salaryCurrency": "USD",

  "daysSincePosted": 2,
  "freshness_tier": "this_week",

  "seniority_normalized": "senior",
  "jobCategory": "marketing",

  "skillsRequired": ["Salesforce", "Hubspot", "Marketo", "Google Sheets"],
  "skillsCount": 4,
  "softSkills": ["Leadership", "Communication"],

  "mentions_equity": true,
  "mentions_health_insurance": true,
  "mentions_unlimited_pto": true,
  "benefitsCount": 3,

  "mentions_diversity": true,
  "mentions_eeo": true,
  "dei_signals_count": 2,

  "pay_transparency_state": "NY",
  "pay_transparency_law": "New York (LL 32 of 2022)",
  "pay_transparency_compliant": true,

  "leadScore": 67,
  "leadTier": "hot",
  "leadScoreReasons": [
    "on 2 job boards",
    "5 roles open",
    "posted this week",
    "salary disclosed",
    "4 skills listed",
    "3 benefits listed"
  ],

  "companyRating": 4.2,
  "jobUrl": "https://www.indeed.com/viewjob?jk=abc123"
}
```

## Use cases

### 🥇 B2B sales prospecting
```python
# Companies hiring across multiple boards = real budget
jobs, _ = client.search(keywords="head of marketing",
                          location="United States",
                          min_lead_score=55,
                          only_with_salary=True)
for j in client.filter_by_lead_tier(jobs, "scorching", "hot"):
    print(j["companyName"], j["jobTitle"])
```

### 🎯 Cross-source winners (strongest budget signal)
```python
# Same role on Indeed AND LinkedIn = serious multi-channel hiring
jobs, _ = client.search(keywords="head of growth",
                          deduplicate_companies=False)
winners = client.filter_cross_source(jobs, min_sources=2)
```

### 💰 CRM-ready CSV export
```python
# 35-column CSV ready for HubSpot/Pipedrive/Salesforce import
jobs, _ = client.search(keywords="sales director",
                          export_format="csv",
                          min_lead_score=40)
# Save to .csv → upload at HubSpot Contacts → Import
```

### 🛠️ Tech-stack targeted outreach
```python
# Find companies hiring for your tech category
jobs, _ = client.search(keywords="devops engineer")
matching = client.filter_by_skills(jobs, "Kubernetes", "Terraform",
                                       match_all=True)
```

### ⚖️ HR-tech compliance audit
```python
# Pay transparency state listings without disclosed salary
jobs, _ = client.search(keywords="manager", location="California")
in_state = client.filter_by_state(jobs, "CA")
non_compliant = [j for j in in_state
                  if j.get("pay_transparency_state") == "CA"
                  and not j.get("pay_transparency_compliant")]
```

### 📈 Hiring trends / market intelligence
```python
# Daily monitoring with cross-run dedup
today, summary = client.search(keywords="data engineer",
                                  only_fresh_this_week=True)
new_listings = client.deduplicate_across_runs(yesterday, today)
```

### 🎯 ABM with ready-to-paste pitches
```python
# 3 outreach variants per top hiring company
top = client.get_top_hiring_companies()
for c in top["top_companies"][:5]:
    pitch = c["outreachPitchVariants"]["consultative"]
    link = c["outreachLinks"]["linkedin_role_owner_search_url"]
```

## Pricing

| Volume | Cost |
|---|---|
| 1 job | $0.003 |
| 100 | $0.30 |
| 1,000 | $3.00 |
| 10,000 | $30.00 |

```python
client.estimate_cost(2_500)   # 7.5 USD
```

The Apify free tier ($5 credit) covers ~1,650 jobs.

## Supported Job Boards

| Source | Default? | Reliability |
|---|---|---|
| **Indeed** | ✅ | High — public listings work consistently |
| **LinkedIn Jobs** | ✅ | High — public search results work consistently |
| **Glassdoor** | ❌ opt-in | Cloudflare-protected, often fails. Add `"glassdoor"` to `sources` if you want to try it |

## Installation

```bash
pip install git+https://github.com/apivault-labs/job-posting-lead-finder-python
```

Or pin to a release tag:

```bash
pip install git+https://github.com/apivault-labs/job-posting-lead-finder-python@v0.1.0
```

## Setup

1. Create an Apify account: <https://console.apify.com/sign-up>
2. Get your API token: <https://console.apify.com/account/integrations>
3. Either pass it explicitly or export `APIFY_API_TOKEN`:

```bash
export APIFY_API_TOKEN="apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

```python
client = JobLeadFinderClient()                        # picks up env var
client = JobLeadFinderClient(api_token="apify_...")   # explicit
```

## Examples

| File | What it shows |
|---|---|
| [`examples/quickstart.py`](examples/quickstart.py) | Basic search with full enrichment breakdown |
| [`examples/bulk_search.py`](examples/bulk_search.py) | Multi-keyword sweep + SUMMARY + TOP_HIRING_COMPANIES digest |
| [`examples/sales_outreach_pipeline.py`](examples/sales_outreach_pipeline.py) | Full prospecting workflow with 3 ready-to-paste pitch variants |
| [`examples/crm_csv_export.py`](examples/crm_csv_export.py) | Direct HubSpot/Salesforce/Pipedrive CSV import |
| [`examples/tech_skills_targeted_outreach.py`](examples/tech_skills_targeted_outreach.py) | Find companies hiring for your tech category |
| [`examples/pay_transparency_compliance_audit.py`](examples/pay_transparency_compliance_audit.py) | HR-tech / legal-tech compliance audit |
| [`examples/daily_monitoring.py`](examples/daily_monitoring.py) | Cross-run dedup with company+title+city fingerprint |
| [`examples/cross_source_winners.py`](examples/cross_source_winners.py) | Companies posting same role on multiple boards |

## API reference

### `JobLeadFinderClient(api_token=None, timeout=900, poll_interval=3.0)`

### `search(keywords, **kwargs) -> (jobs, summary)`

Forwards all 14 actor input flags. See full list in
[`job_lead_finder/client.py`](job_lead_finder/client.py).

Key parameters:
- `location`, `sources` (default `("indeed", "linkedin")`)
- `deduplicate_companies` (default True)
- `min_lead_score` (0-100), `only_with_salary`, `only_remote`,
  `only_fresh_this_week`, `only_pay_transparency_compliant`
- `export_format` (`default` / `csv`)
- `write_summary`, `top_n` (5-100)

### KV record helpers

- `get_summary() -> dict | None`
- `get_top_hiring_companies() -> dict | None`
- `get_top_jobs() -> dict | None`

### Filters (return new lists)

- `filter_by_lead_tier(jobs, *tiers)` — cold/warm/hot/scorching
- `filter_by_seniority(jobs, *levels)`
- `filter_by_category(jobs, *categories)`
- `filter_by_salary_tier(jobs, *tiers)`
- `filter_by_min_salary(jobs, min_usd)`
- `filter_by_state(jobs, *states)` — US 2-letter codes
- `filter_remote(jobs)`
- `filter_with_pay_transparency(jobs)`
- `filter_diverse_employers(jobs, min_signals=2)`
- `filter_by_skills(jobs, *skills, match_all=False)`
- `filter_by_freshness(jobs, *tiers)`
- `filter_cross_source(jobs, min_sources=2)`
- `filter_by_source(jobs, *sources)` — indeed/linkedin/glassdoor
- `filter_with_benefits(jobs, *benefits, match_all=False)`

### Helpers

- `estimate_cost(expected_jobs) -> float`
- `deduplicate_across_runs(previous, new) -> list` — uses
  company+title+city fingerprint, matches the actor's internal logic

## How it works

```
your_code → JobLeadFinderClient → Apify API
                                     ↓
                             Apify actor v1.2
                                     ↓
                       Multi-source fan-out (parallel)
                                     ↓
            ┌────────────────┬───────┴──────────┐
        Indeed              LinkedIn         Glassdoor (opt-in)
            ↓                  ↓                  ↓
            └──── Thunderbit (rendering) ─────────┘
                                     ↓
              Cross-source dedup by company+title+city
                                     ↓
              12-layer enrichment (salary/skills/seniority/...)
                                     ↓
                          Server-side filters
                                     ↓
                     default JSON / flat 35-column CSV
                                     ↓
              + SUMMARY + TOP_HIRING_COMPANIES + TOP_JOBS in KV
                                     ↓
                                 you, in Python
```

## FAQ

**Q: Why is Glassdoor opt-in?**
A: Glassdoor uses Cloudflare anti-bot. Default sources are Indeed +
LinkedIn (both consistently work). Add `"glassdoor"` to `sources` if
you want to try it — transient failures log a warning, don't break
the run.

**Q: How is this better than scraping each board separately?**
A: Cross-source dedup collapses duplicates by company+title+city, so
you only pay $0.003 once even if a job appears on 2 boards. Plus
unified schema across boards and `sources_seen[]` as a leadScore
signal.

**Q: How accurate is `leadScore`?**
A: Heuristic — companies appearing on multiple boards with multiple
fresh listings, disclosed salaries, and senior roles score highest.
Treat `scorching` and `hot` as priority outreach.

**Q: Can I get the salary even if Indeed didn't show it?**
A: Yes — when the same job appears on multiple boards, the actor
smart-merges fields. Salary may be on LinkedIn but missing on Indeed,
or vice versa. The merged record gets the disclosed value from
whichever source had it.

**Q: How do I import into HubSpot/Salesforce/Pipedrive?**
A: Use `export_format="csv"`. See
[`examples/crm_csv_export.py`](examples/crm_csv_export.py).

**Q: Will I get blocked / banned?**
A: All scraping happens on Apify infrastructure via Thunderbit's
whitelisted pool. Your IP is never touched.

**Q: How is this better than Apollo / ZoomInfo / RocketReach?**
A: Pay-as-you-go ($0.003/job vs $99-300+/mo subscription). Real-time
hiring data — Apollo's "intent data" is laggy. Built-in pitch
generation (3 tone variants per company). Direct CSV import. No seat
fees.

**Q: How fresh is the data?**
A: Real-time — scraped live at run time.

## Detected vocabularies

The actor uses fixed regex vocabularies (no AI / no LLM) so results
are deterministic and predictable. See the
[actor README](https://apify.com/apivault_labs/apify-actor-job-leads)
for the full lists:

- 225 tech skills (Python, React, Postgres, AWS, Salesforce, ...)
- 15 soft skills, 18 certifications
- 15 job categories with curated regex per category
- 10 seniority buckets
- 14 benefit boolean flags
- 7 DEI signals
- 12 US pay-transparency states
- 7 currencies + FX rates

## Keywords

`indeed-scraper` `indeed-jobs` `linkedin-jobs` `linkedin-without-login`
`glassdoor-jobs` `job-scraper` `job-aggregator` `job-search-api`
`lead-generation` `b2b-prospecting` `sales-prospecting`
`hiring-signals` `outreach-automation` `cold-email` `cold-outreach`
`hubspot-enrichment` `salesforce-import` `pipedrive-import`
`apollo-alternative` `zoominfo-alternative` `rocketreach-alternative`
`sales-navigator-alternative`
`salary-parser` `salary-benchmarking` `compensation-data`
`skills-extraction` `recruitment-tech` `ats-data` `sourcing-tool`
`remote-jobs-api` `diversity-hiring` `pay-transparency`
`apify` `python-sdk`

## License

MIT — see [LICENSE](LICENSE).
