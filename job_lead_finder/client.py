"""
JobLeadFinderClient — synchronous wrapper around the Apify
``apivault_labs/apify-actor-job-leads`` actor (v1.2).

The actor handles all heavy work on Apify infrastructure:
  - Multi-source fan-out (Indeed + LinkedIn + opt-in Glassdoor) via Thunderbit
  - Cross-source dedup by company+title+city fingerprint
  - 12-layer enrichment: salary parser (7 currencies + FX),
    skills extraction (225 tech / 15 soft / 18 certifications),
    14 benefit flags, 15 job categories, 11 seniority buckets,
    location parser, 7 DEI signals, 12-state US pay-transparency law
  - leadScore 0-100 with cross-source presence × hiring volume signals
  - 3-variant outreach pitches per company (consultative / aggressive /
    referral)
  - Server-side filters and CSV export for direct CRM import
  - SUMMARY + TOP_HIRING_COMPANIES + TOP_JOBS to KV store

This client forwards inputs, polls until the run finishes, then
downloads the dataset and exposes filters & helpers for sales-ops
workflows.

Pricing: $0.003 per job ($3 / 1000). All enrichment included.

Quick start:

    from job_lead_finder import JobLeadFinderClient

    client = JobLeadFinderClient(api_token="apify_api_xxxxxx")

    jobs, summary = client.search(
        keywords="marketing manager",
        location="New York, NY",
        min_lead_score=55,
    )

    for j in client.filter_by_lead_tier(jobs, "scorching", "hot"):
        print(j["companyName"], j["jobTitle"], j.get("salary_tier"))
"""

from __future__ import annotations

import os
import time
from typing import Any, Sequence

import requests

from .exceptions import (
    ActorRunError,
    ActorTimeoutError,
    AuthenticationError,
    JobLeadFinderError,
)


ACTOR_ID = "apivault_labs~apify-actor-job-leads"
APIFY_API_BASE = "https://api.apify.com/v2"

TERMINAL_OK = {"SUCCEEDED"}
TERMINAL_FAIL = {"FAILED", "TIMED-OUT", "ABORTED"}

PRICE_PER_JOB_USD = 0.003

VALID_SOURCES = ("indeed", "linkedin", "glassdoor")
VALID_EXPORT_FORMATS = ("default", "csv")


class JobLeadFinderClient:
    """Synchronous client for the Job Posting Lead Finder Apify actor.

    Parameters
    ----------
    api_token : str, optional
        Apify Personal API token. Falls back to ``APIFY_API_TOKEN``.
    timeout : int, optional
        Maximum seconds to wait for an actor run. Default 900 (15 min) —
        a 2-source run with default config takes ~30s.
    poll_interval : float, optional
        Seconds between status polls. Default 3.
    base_url : str, optional
        Override the Apify API base URL.
    """

    def __init__(
        self,
        api_token: str | None = None,
        timeout: int = 900,
        poll_interval: float = 3.0,
        base_url: str = APIFY_API_BASE,
    ):
        token = api_token or os.environ.get("APIFY_API_TOKEN")
        if not token:
            raise AuthenticationError(
                "Apify API token is required. Pass api_token='apify_api_...' "
                "or set the APIFY_API_TOKEN environment variable. "
                "Get a token at https://console.apify.com/account/integrations"
            )
        self._token = token
        self._timeout = int(timeout)
        self._poll_interval = float(poll_interval)
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "User-Agent": "job-posting-lead-finder-python/0.1.0",
        })
        self._last_run_id: str | None = None
        self._last_dataset_id: str | None = None
        self._last_kvs_id: str | None = None

    # ------------------------------------------------------------------ public

    def search(
        self,
        keywords: str,
        *,
        location: str = "",
        sources: Sequence[str] = ("indeed", "linkedin"),
        # Dedup
        deduplicate_companies: bool = True,
        # Server-side filters
        min_lead_score: int = 0,
        only_with_salary: bool = False,
        only_remote: bool = False,
        only_fresh_this_week: bool = False,
        only_pay_transparency_compliant: bool = False,
        # Export
        export_format: str = "default",
        write_summary: bool = True,
        top_n: int = 20,
        # Plumbing
        thunderbit_retries: int = 1,
        max_concurrency: int = 3,
        timeout_per_source: int = 120,
        actor_timeout_secs: int = 600,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Run a job search across the requested boards and return enriched
        results.

        Parameters
        ----------
        keywords : str
            Job title or keywords (e.g. ``"marketing manager"``).
            Required.
        location : str, optional
            City, state, country, or ``"Remote"``.
        sources : Sequence[str], optional
            Subset of ``("indeed", "linkedin", "glassdoor")``. Default
            keeps Indeed + LinkedIn (the most reliable). Glassdoor
            often fails on Cloudflare; opt in only if you accept that.
        deduplicate_companies : bool, optional
            Keep one job per company (highest leadScore). Disable to
            keep every role for richer hiring-volume data. Default True.
        min_lead_score : int, optional
            Drop jobs below this leadScore (0-100). 0 = no filter.
        only_with_salary, only_remote, only_fresh_this_week,
        only_pay_transparency_compliant : bool, optional
            Server-side post-filters.
        export_format : str, optional
            ``"default"`` (full JSON, 40+ fields) or ``"csv"``
            (35-column flat row ready for HubSpot/Salesforce/Pipedrive).
        write_summary : bool, optional
            Write SUMMARY + TOP_HIRING_COMPANIES + TOP_JOBS to KV store.
        top_n : int, optional
            Size of TOP_HIRING_COMPANIES + TOP_JOBS records (5-100).

        Returns
        -------
        tuple[list[dict], dict | None]
            ``(jobs, summary)`` — ``summary`` is the SUMMARY KV record
            or ``None`` if ``write_summary`` was disabled.
        """
        if not keywords or not keywords.strip():
            raise ValueError("keywords must be a non-empty string")

        cleaned_sources = [
            s.lower().strip() for s in sources
            if s and s.lower().strip() in VALID_SOURCES
        ]
        if not cleaned_sources:
            raise ValueError(
                f"sources must include at least one of {VALID_SOURCES}"
            )

        if export_format not in VALID_EXPORT_FORMATS:
            raise ValueError(
                f"export_format must be one of {VALID_EXPORT_FORMATS}, "
                f"got {export_format!r}"
            )

        payload = {
            "keywords": keywords.strip(),
            "location": location or "",
            "sources": cleaned_sources,
            "deduplicateCompanies": bool(deduplicate_companies),
            "minLeadScore": max(0, min(100, int(min_lead_score))),
            "onlyWithSalary": bool(only_with_salary),
            "onlyRemote": bool(only_remote),
            "onlyFreshThisWeek": bool(only_fresh_this_week),
            "onlyPayTransparencyCompliant": bool(
                only_pay_transparency_compliant
            ),
            "exportFormat": export_format,
            "writeSummary": bool(write_summary),
            "topN": max(5, min(100, int(top_n))),
            "thunderbitRetries": max(0, min(3, int(thunderbit_retries))),
            "maxConcurrency": max(1, min(5, int(max_concurrency))),
            "timeout": max(30, min(300, int(timeout_per_source))),
        }

        run_id = self._start_run(
            payload, actor_timeout_secs=actor_timeout_secs
        )
        run = self._wait_for_run(run_id)
        self._last_run_id = run_id
        self._last_dataset_id = run.get("defaultDatasetId")
        self._last_kvs_id = run.get("defaultKeyValueStoreId")
        records = self._fetch_dataset(self._last_dataset_id)

        summary = None
        if write_summary and self._last_kvs_id:
            summary = self._fetch_kv_record(self._last_kvs_id, "SUMMARY")

        return records, summary

    # ------------------------------------------------------------------ KV helpers

    def get_summary(self) -> dict[str, Any] | None:
        """Fetch the aggregate ``SUMMARY`` record from the most recent run."""
        if not self._last_kvs_id:
            return None
        return self._fetch_kv_record(self._last_kvs_id, "SUMMARY")

    def get_top_hiring_companies(self) -> dict[str, Any] | None:
        """Fetch the ``TOP_HIRING_COMPANIES`` snapshot from the most
        recent run.

        Top N companies sorted by job count, each with:
        ``jobs_count``, ``sources_active[]``, ``max_leadScore``,
        ``categories``, ``top_skills``, ``avg_salary_usd``,
        ``outreachPitch``, ``outreachPitchVariants``
        (consultative / aggressive / referral), ``outreachLinks``.
        """
        if not self._last_kvs_id:
            return None
        return self._fetch_kv_record(
            self._last_kvs_id, "TOP_HIRING_COMPANIES"
        )

    def get_top_jobs(self) -> dict[str, Any] | None:
        """Fetch the ``TOP_JOBS`` snapshot — top N jobs sorted by leadScore
        (per-job sales-ops digest)."""
        if not self._last_kvs_id:
            return None
        return self._fetch_kv_record(self._last_kvs_id, "TOP_JOBS")

    # ------------------------------------------------------------------ filters

    def filter_by_lead_tier(
        self,
        jobs: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter to jobs whose ``leadTier`` is in the requested set.

        Tiers: ``cold`` / ``warm`` / ``hot`` / ``scorching``. Default
        keeps ``("scorching", "hot")``.
        """
        if not tiers:
            tiers = ("scorching", "hot")
        wanted = {t.lower() for t in tiers}
        return [
            j for j in jobs
            if (j.get("leadTier") or "").lower() in wanted
        ]

    def filter_by_seniority(
        self,
        jobs: Sequence[dict[str, Any]],
        *levels: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``seniority_normalized`` (intern / junior / mid /
        senior / lead / staff / principal / director / vp / c-level)."""
        if not levels:
            return list(jobs)
        wanted = {lv.lower() for lv in levels}
        return [
            j for j in jobs
            if (j.get("seniority_normalized") or "").lower() in wanted
        ]

    def filter_by_category(
        self,
        jobs: Sequence[dict[str, Any]],
        *categories: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``jobCategory`` (engineering / sales / marketing /
        ...)."""
        if not categories:
            return list(jobs)
        wanted = {c.lower() for c in categories}
        return [
            j for j in jobs
            if (j.get("jobCategory") or "").lower() in wanted
        ]

    def filter_by_salary_tier(
        self,
        jobs: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``salary_tier`` (entry / mid / senior / principal /
        unicorn)."""
        if not tiers:
            return list(jobs)
        wanted = {t.lower() for t in tiers}
        return [
            j for j in jobs
            if (j.get("salary_tier") or "").lower() in wanted
        ]

    def filter_by_min_salary(
        self,
        jobs: Sequence[dict[str, Any]],
        min_usd: int,
    ) -> list[dict[str, Any]]:
        """Keep only jobs whose ``salaryMedianUsd`` is at least ``min_usd``."""
        return [
            j for j in jobs
            if (j.get("salaryMedianUsd") or 0) >= min_usd
        ]

    def filter_by_state(
        self,
        jobs: Sequence[dict[str, Any]],
        *states: str,
    ) -> list[dict[str, Any]]:
        """Filter by US state (2-letter codes via
        ``parsedLocation.state``)."""
        wanted = {s.upper() for s in states if s}
        if not wanted:
            return list(jobs)
        return [
            j for j in jobs
            if ((j.get("parsedLocation") or {}).get("state") or "").upper()
                in wanted
        ]

    def filter_remote(
        self,
        jobs: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to fully-remote jobs (``workMode == "remote"`` or
        ``isRemoteListing``)."""
        out: list[dict[str, Any]] = []
        for j in jobs:
            if j.get("workMode") == "remote":
                out.append(j)
            elif j.get("isRemoteListing"):
                out.append(j)
        return out

    def filter_with_pay_transparency(
        self,
        jobs: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to jobs in pay-transparency law states with disclosed
        salary."""
        return [
            j for j in jobs
            if j.get("pay_transparency_state")
            and j.get("pay_transparency_compliant")
        ]

    def filter_diverse_employers(
        self,
        jobs: Sequence[dict[str, Any]],
        min_signals: int = 2,
    ) -> list[dict[str, Any]]:
        """Filter to employers signaling commitment to DEI (≥ N signals
        out of 7)."""
        return [
            j for j in jobs
            if (j.get("dei_signals_count") or 0) >= min_signals
        ]

    def filter_by_skills(
        self,
        jobs: Sequence[dict[str, Any]],
        *skills: str,
        match_all: bool = False,
    ) -> list[dict[str, Any]]:
        """Filter to jobs requiring any (or all) of the given skills.

        Case-insensitive substring match against ``skillsRequired[]``.
        """
        if not skills:
            return list(jobs)
        needles = [s.lower() for s in skills if s]
        out: list[dict[str, Any]] = []
        for j in jobs:
            stack = [s.lower() for s in (j.get("skillsRequired") or [])]
            if not stack:
                continue
            if match_all:
                if all(any(n in s for s in stack) for n in needles):
                    out.append(j)
            else:
                if any(any(n in s for s in stack) for n in needles):
                    out.append(j)
        return out

    def filter_by_freshness(
        self,
        jobs: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``freshness_tier``
        (today / this_week / this_month / older)."""
        if not tiers:
            tiers = ("today", "this_week")
        wanted = {t.lower() for t in tiers}
        return [
            j for j in jobs
            if (j.get("freshness_tier") or "").lower() in wanted
        ]

    def filter_cross_source(
        self,
        jobs: Sequence[dict[str, Any]],
        min_sources: int = 2,
    ) -> list[dict[str, Any]]:
        """Filter to jobs that appeared on multiple boards (cross-source
        hiring effort = serious budget signal)."""
        return [
            j for j in jobs
            if len(j.get("sources_seen") or []) >= min_sources
        ]

    def filter_by_source(
        self,
        jobs: Sequence[dict[str, Any]],
        *sources: str,
    ) -> list[dict[str, Any]]:
        """Filter to jobs whose primary source is one of the requested
        boards (``indeed`` / ``linkedin`` / ``glassdoor``)."""
        if not sources:
            return list(jobs)
        wanted = {s.lower() for s in sources}
        return [
            j for j in jobs
            if (j.get("source") or "").lower() in wanted
        ]

    def filter_with_benefits(
        self,
        jobs: Sequence[dict[str, Any]],
        *benefit_keys: str,
        match_all: bool = False,
    ) -> list[dict[str, Any]]:
        """Filter to jobs that mention specific benefits.

        ``benefit_keys`` are bare names like ``"equity"``, ``"401k"``,
        ``"unlimited_pto"``, ``"visa_sponsorship"`` (no ``mentions_``
        prefix needed). Default ``match_all=False`` requires at least
        one match.
        """
        if not benefit_keys:
            return list(jobs)
        wanted_keys = [
            f"mentions_{k.lstrip('mentions_').lstrip('_')}"
            for k in benefit_keys
        ]
        out: list[dict[str, Any]] = []
        for j in jobs:
            hits = [bool(j.get(k)) for k in wanted_keys]
            if match_all and all(hits):
                out.append(j)
            elif not match_all and any(hits):
                out.append(j)
        return out

    # ------------------------------------------------------------------ helpers

    def estimate_cost(self, expected_jobs: int) -> float:
        """Estimate USD cost for ``expected_jobs`` jobs at $3 / 1000.

        Use this *before* calling :meth:`search` to budget your run.
        Each board returns up to ~60 jobs per search; expect 50-150
        unique jobs after dedup.
        """
        return round(expected_jobs * PRICE_PER_JOB_USD, 4)

    def deduplicate_across_runs(
        self,
        previous_jobs: Sequence[dict[str, Any]],
        new_jobs: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Drop jobs from ``new_jobs`` that already appeared in
        ``previous_jobs``.

        Uses a ``companyName + jobTitle + city`` fingerprint (the same
        one the actor uses internally) so this works even when source
        boards renumber URLs.
        """
        def fp(j: dict[str, Any]) -> str:
            title = (j.get("jobTitle") or "").strip().lower()[:80]
            company = (j.get("companyName") or "").strip().lower()
            parsed = j.get("parsedLocation") or {}
            city = (parsed.get("city")
                    or j.get("location") or "").strip().lower()[:40]
            return f"{company}|{title}|{city}"

        seen = {fp(j) for j in previous_jobs}
        return [j for j in new_jobs if fp(j) not in seen]

    # ------------------------------------------------------------------ private

    def _start_run(
        self,
        payload: dict[str, Any],
        actor_timeout_secs: int,
    ) -> str:
        url = f"{self._base_url}/acts/{ACTOR_ID}/runs"
        params = {"timeout": int(actor_timeout_secs)}
        try:
            r = self._session.post(
                url, params=params, json=payload, timeout=30
            )
        except requests.RequestException as e:
            raise JobLeadFinderError(
                f"Failed to start actor run: {e}"
            ) from e
        if r.status_code == 401:
            raise AuthenticationError(
                "Apify rejected the API token. Generate a new one at "
                "https://console.apify.com/account/integrations"
            )
        if r.status_code >= 400:
            raise ActorRunError(
                f"Apify returned HTTP {r.status_code} when starting run: "
                f"{r.text[:300]}"
            )
        data = r.json().get("data") or {}
        run_id = data.get("id")
        if not run_id:
            raise ActorRunError(
                f"Apify response missing run id: {r.text[:300]}"
            )
        return run_id

    def _wait_for_run(self, run_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/actor-runs/{run_id}"
        deadline = time.time() + self._timeout
        while True:
            try:
                r = self._session.get(url, timeout=30)
            except requests.RequestException as e:
                raise JobLeadFinderError(
                    f"Failed to poll run status: {e}"
                ) from e
            if r.status_code >= 400:
                raise ActorRunError(
                    f"Apify returned HTTP {r.status_code} when polling: "
                    f"{r.text[:300]}"
                )
            run = r.json().get("data") or {}
            status = run.get("status")
            if status in TERMINAL_OK:
                return run
            if status in TERMINAL_FAIL:
                raise ActorRunError(
                    f"Actor run {run_id} ended with status={status}: "
                    f"{run.get('statusMessage') or '(no message)'}"
                )
            if time.time() > deadline:
                raise ActorTimeoutError(
                    f"Actor run {run_id} did not finish within "
                    f"{self._timeout}s (last status={status}). Increase "
                    "`timeout=` or fetch the dataset manually."
                )
            time.sleep(self._poll_interval)

    def _fetch_dataset(self, dataset_id: str) -> list[dict[str, Any]]:
        url = f"{self._base_url}/datasets/{dataset_id}/items"
        params = {"clean": "true", "format": "json"}
        try:
            r = self._session.get(url, params=params, timeout=120)
        except requests.RequestException as e:
            raise JobLeadFinderError(
                f"Failed to download dataset: {e}"
            ) from e
        if r.status_code >= 400:
            raise ActorRunError(
                f"Apify returned HTTP {r.status_code} when fetching "
                f"dataset: {r.text[:300]}"
            )
        try:
            data = r.json()
        except ValueError as e:
            raise ActorRunError(
                f"Apify dataset is not valid JSON: {e}"
            ) from e
        if not isinstance(data, list):
            raise ActorRunError(
                f"Unexpected dataset payload: {type(data).__name__}"
            )
        return data

    def _fetch_kv_record(self, kvs_id: str, key: str) -> dict[str, Any] | None:
        url = f"{self._base_url}/key-value-stores/{kvs_id}/records/{key}"
        try:
            r = self._session.get(url, timeout=30)
        except requests.RequestException:
            return None
        if r.status_code >= 400:
            return None
        try:
            return r.json()
        except ValueError:
            return None
