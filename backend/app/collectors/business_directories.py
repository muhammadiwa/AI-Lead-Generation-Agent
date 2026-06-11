"""Business directory scraper — Crunchbase, Product Hunt, Yelp, and other directories."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_headers, proxy_rotator, rate_limiter

logger = logging.getLogger(__name__)


class BusinessDirectoryCollector(BaseCollector):
    """Collect leads from business directories like Product Hunt, Yelp, and SaaS directories."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "business_directory"
        rate_limiter.register_source("directories", rate=3.0, burst=5)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        directories = query.get("directories", ["producthunt", "yelp", "saas1000"])
        categories = query.get(
            "categories",
            ["software", "developer-tools", "saas", "analytics", "productivity"],
        )

        if "producthunt" in directories:
            ph_leads = await self._scrape_producthunt(categories, max_results // 3)
            leads.extend(ph_leads)

        if "yelp" in directories:
            yelp_leads = await self._scrape_yelp(query, max_results // 3)
            leads.extend(yelp_leads)

        if "saas1000" in directories:
            saas_leads = await self._scrape_saas_directory(max_results // 3)
            leads.extend(saas_leads)

        return leads[:max_results]

    async def _scrape_producthunt(self, categories: List[str], max_results: int) -> List[CollectedLead]:
        """Scrape Product Hunt for new products (companies building software)."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for category in categories[:3]:
                if len(leads) >= max_results:
                    break
                await rate_limiter.wait("directories")
                await async_random_delay(2.0, 4.0)

                try:
                    proxy = proxy_rotator.random()
                    resp = await client.get(
                        f"https://www.producthunt.com/categories/{category}",
                        headers=build_headers(),
                        proxies=proxy,
                    )

                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        # Extract company/product names
                        for link in soup.select('a[href*="/posts/"]')[:15]:
                            text = link.get_text(strip=True)
                            href = link.get("href", "")
                            if text and len(text) > 2:
                                lead = CollectedLead(
                                    company_name=text,
                                    company_url=f"https://www.producthunt.com{href}" if href.startswith("/") else href,
                                    source="business_directory",
                                    source_url="https://www.producthunt.com",
                                    confidence=0.5,
                                )
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"ProductHunt scrape failed for category '{category}': {e}")

        return leads

    async def _scrape_yelp(self, query: Dict[str, Any], max_results: int) -> List[CollectedLead]:
        """Scrape Yelp for businesses in software/tech categories."""
        leads: List[CollectedLead] = []
        search_terms = query.get(
            "search_terms",
            ["software development", "web development", "mobile app development", "IT consulting"],
        )
        locations = query.get("locations", ["San Francisco", "New York", "Austin"])

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for term in search_terms[:3]:
                for location in locations[:2]:
                    if len(leads) >= max_results:
                        break
                    await rate_limiter.wait("directories")
                    await async_random_delay(2.0, 4.0)

                    try:
                        proxy = proxy_rotator.random()
                        resp = await client.get(
                            "https://www.yelp.com/search",
                            params={"find_desc": term, "find_loc": location},
                            headers=build_headers(),
                            proxies=proxy,
                        )

                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, "lxml")
                            for biz in soup.select('[data-testid="businessName"]')[:10]:
                                name = biz.get_text(strip=True)
                                parent_link = biz.find_parent("a")
                                href = parent_link.get("href", "") if parent_link else ""
                                lead = CollectedLead(
                                    company_name=name,
                                    company_url=f"https://www.yelp.com{href}" if href.startswith("/") else href,
                                    source="business_directory",
                                    source_url="https://www.yelp.com",
                                    confidence=0.5,
                                )
                                leads.append(lead)
                    except Exception as e:
                        logger.warning(f"Yelp scrape failed for '{term}' in '{location}': {e}")

        return leads

    async def _scrape_saas_directory(self, max_results: int) -> List[CollectedLead]:
        """Scrape SaaS directories for companies in the space."""
        leads: List[CollectedLead] = []
        urls = [
            "https://www.saas1000.com",
            "https://www.g2.com/categories/software-development",
        ]

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for url in urls:
                if len(leads) >= max_results:
                    break
                await rate_limiter.wait("directories")
                await async_random_delay(2.0, 3.0)

                try:
                    resp = await client.get(url, headers=build_headers())
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        # Extract company names from common patterns
                        for link in soup.select("a[href*='/company/'], a[href*='/product/']")[:20]:
                            text = link.get_text(strip=True)
                            if text and len(text) > 2 and len(text) < 100:
                                lead = CollectedLead(
                                    company_name=text,
                                    source="business_directory",
                                    source_url=url,
                                    confidence=0.4,
                                )
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"Directory scrape failed for {url}: {e}")

        return leads