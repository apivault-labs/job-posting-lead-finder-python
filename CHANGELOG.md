# Changelog

## [0.1.0] — 2026-05-23

Initial release of the Python SDK for the Job Posting Lead Finder
Apify actor (v1.2).

### Added

- `JobLeadFinderClient` with `search()` and **12 client-side filter
  helpers**:
  - `filter_by_lead_tier(jobs, *tiers)` — cold/warm/hot/scorching
  - `filter_by_seniority(jobs, *levels)` — intern → c-level
  - `filter_by_category(jobs, *categories)` — engineering / sales / ...
  - `filter_by_salary_tier(jobs, *tiers)` — entry/mid/senior/principal/unicorn
  - `filter_by_min_salary(jobs, min_usd)`
  - `filter_by_state(jobs, *states)` — US 2-letter codes
  - `filter_remote(jobs)` — fully-remote
  - `filter_with_pay_transparency(jobs)` — disclosed salary +
    applicable law
  - `filter_diverse_employers(jobs, min_signals=2)`
  - `filter_by_skills(jobs, *skills, match_all=False)`
  - `filter_by_freshness(jobs, *tiers)` — today/this_week/this_month/older
  - `filter_cross_source(jobs, min_sources=2)` — cross-board hiring
    signal (= active multi-channel budget)
  - `filter_by_source(jobs, *sources)` — indeed / linkedin / glassdoor
  - `filter_with_benefits(jobs, *benefits, match_all=False)` — equity,
    visa_sponsorship, unlimited_pto, ...
- KV record helpers: `get_summary()`, `get_top_hiring_companies()`,
  `get_top_jobs()`
- `deduplicate_across_runs()` for daily monitoring loops (uses
  company+title+city fingerprint, matching the actor's internal logic)
- `estimate_cost(expected_jobs)` for pre-run budgeting
- All 14 actor input flags exposed as keyword arguments
- 8 example scripts:
  - `quickstart.py`
  - `bulk_search.py` — multi-keyword run with SUMMARY +
    TOP_HIRING_COMPANIES + TOP_JOBS digest
  - `sales_outreach_pipeline.py` — full prospecting workflow with
    3 ready-to-paste pitch variants
  - `crm_csv_export.py` — direct HubSpot/Salesforce/Pipedrive import
  - `tech_skills_targeted_outreach.py` — find companies hiring for
    Salesforce/Kubernetes/etc, pitch your tech category
  - `pay_transparency_compliance_audit.py` — HR-tech / legal-tech
    use case
  - `daily_monitoring.py` — cross-run dedup with company+title+city
    fingerprint
  - `cross_source_winners.py` — companies that posted the same role
    on Indeed AND LinkedIn (= serious budget signal)
- MIT license
