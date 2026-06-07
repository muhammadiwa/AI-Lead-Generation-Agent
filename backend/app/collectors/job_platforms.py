"""Job platform monitor — discovers leads from Upwork, Freelancer, Fiverr, and LinkedIn Jobs.
Companies posting development jobs are potential leads for software development services.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_headers, proxy_rotator, rate_limiter

logger = logging.getLogger(__name__)


class JobPlatformCollector(BaseCollector):
    """Monitor job platforms for companies hiring developers — strong lead signals."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "job_platforms"
        rate_limiter.register_source("job_boards", rate=3.0, burst=5)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        job_titles = query.get(
            "job_titles",
            [
                "software engineer",
                "full stack developer",
                "CTO",
                "VP Engineering",
                "tech lead",
                "backend developer",
            ],
        )
        platforms = query.get("platforms", ["linkedin_jobs", "remoteok", "weworkremotely"])

        if "linkedin_jobs" in platforms:
            linkedin_leads = await self._scrape_linkedin_jobs(job_titles, max_results // 3)
            leads.extend(linkedin_leads)

        if "remoteok" in platforms:
            remoteok_leads = await self._scrape_remoteok(job_titles, max_results // 3)
            leads.extend(remoteok_leads)

        if "weworkremotely" in platforms:
            wwr_leads = await self._scrape_weworkremotely(job_titles, max_results // 3)
            leads.extend(wwr_leads)

        return leads[:max_results]

    async def _scrape_linkedin_jobs(self, job_titles: List[str], max_results: int) -> List[CollectedLead]:
        """Scrape LinkedIn Jobs for companies hiring in tech roles."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for title in job_titles[:5]:
                if len(leads) >= max_results:
                    break
                await rate_limiter.wait("job_boards")
                await async_random_delay(3.0, 5.0)

                try:
                    proxy = proxy_rotator.random()
                    resp = await client.get(
                        "https://www.linkedin.com/jobs/search/",
                        params={"keywords": title, "location": "United States"},
                        headers=build_headers(referer="https://www.linkedin.com"),
                        proxies=proxy,
                    )

                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        # Extract company names from job listings
                        company_elements = soup.select(".job-card-container__company-name")
                        for elem in company_elements[:10]:
                            company_name = elem.get_text(strip=True)
                            if company_name and len(company_name) > 1:
                                lead = CollectedLead(
                                    company_name=company_name,
                                    source="job_platforms",
                                    source_url="https://www.linkedin.com/jobs",
                                    confidence=0.6,
                                )
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"LinkedIn Jobs scrape failed for '{title}': {e}")

        return leads

    async def _scrape_remoteok(self, job_titles: List[str], max_results: int) -> List[CollectedLead]:
        """Scrape RemoteOK for companies hiring remote devs."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for title in job_titles[:3]:
                if len(leads) >= max_results:
                    break
                await rate_limiter.wait("job_boards")
                await async_random_delay(2.0, 3.0)

                try:
                    resp = await client.get(
                        "https://remoteok.com",
                        params={"s": title},
                        headers=build_headers(),
                    )

                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        for row in soup.select("tr.job")[:20]:
                            company_elem = row.select_one(".companyLink h3")
                            if company_elem:
                                company_name = company_elem.get_text(strip=True)
                                lead = CollectedLead(
                                    company_name=company_name,
                                    source="job_platforms",
                                    source_url="https://remoteok.com",
                                    confidence=0.5,
                                )
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"RemoteOK scrape failed for '{title}': {e}")

        return leads

    async def _scrape_weworkremotely(self, job_titles: List[str], max_results: int) -> List[CollectedLead]:
        """Scrape WeWorkRemotely for companies hiring remote devs."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for title in job_titles[:3]:
                if len(leads) >= max_results:
                    break
                await rate_limiter.wait("job_boards")
                await async_random_delay(2.0, 3.0)

                try:
                    resp = await client.get(
                        "https://weworkremotely.com",
                        headers=build_headers(),
                    )

                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        for li in soup.select("li")[:30]:
                            company_elem = li.select_one(".company-name, span.company")
                            if company_elem:
                                company_name = company_elem.get_text(strip=True)
                                if company_name and len(company_name) > 1:
                                    lead = CollectedLead(
                                        company_name=company_name,
                                        source="job_platforms",
                                        source_url="https://weworkremotely.com",
                                        confidence=0.5,
                                    )
                                    leads.append(lead)
                except Exception as e:
                    logger.warning(f"WWR scrape failed for '{title}': {e}")

        return leads