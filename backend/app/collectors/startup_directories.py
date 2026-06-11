"""AngelList & Startup Directories collector.

Scrapes AngelList (Wellfound), Y Combinator companies, and other startup
directories to discover tech companies that may need development services.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_headers, proxy_rotator, rate_limiter

logger = logging.getLogger(__name__)


class StartupDirectoryCollector(BaseCollector):
    """Collect leads from AngelList, Y Combinator, and startup directories."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "startup_directories"
        rate_limiter.register_source("directories", rate=3.0, burst=5)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        directories = query.get("directories", ["angellist", "yc", "wellfound"])

        if "angellist" in directories or "wellfound" in directories:
            al_leads = await self._scrape_angellist(query, max_results // 3)
            leads.extend(al_leads)

        if "yc" in directories:
            yc_leads = await self._scrape_ycombinator(query, max_results // 3)
            leads.extend(yc_leads)

        return leads[:max_results]

    async def _scrape_angellist(self, query: Dict[str, Any], max_results: int) -> List[CollectedLead]:
        """Scrape AngelList/Wellfound for tech startup companies."""
        leads: List[CollectedLead] = []
        search_terms = query.get("search_terms", ["software", "saas", "ai", "developer tools"])

        for term in search_terms[:3]:
            if len(leads) >= max_results:
                break
            await rate_limiter.wait("directories")
            await async_random_delay(3.0, 5.0)

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                try:
                    proxy = proxy_rotator.random()
                    resp = await client.get(
                        "https://wellfound.com/search/companies",
                        params={"q": term},
                        headers=build_headers(referer="https://wellfound.com"),
                        proxies=proxy,
                    )

                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        for card in soup.select("div[class*='startup'], div[class*='company'], article, li[class*='startup']")[:15]:
                            lead = self._parse_angellist_card(card)
                            if lead:
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"AngelList scrape failed for '{term}': {e}")

        return leads

    async def _scrape_ycombinator(self, query: Dict[str, Any], max_results: int) -> List[CollectedLead]:
        """Scrape Y Combinator companies directory."""
        leads: List[CollectedLead] = []

        await rate_limiter.wait("directories")
        await async_random_delay(2.0, 4.0)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                proxy = proxy_rotator.random()
                resp = await client.get(
                    "https://www.ycombinator.com/companies/",
                    headers=build_headers(referer="https://www.ycombinator.com"),
                    proxies=proxy,
                )

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    for card in soup.select("a[class*='company'], div[class*='company']")[:20]:
                        lead = self._parse_yc_card(card)
                        if lead:
                            leads.append(lead)
            except Exception as e:
                logger.warning(f"YC scrape failed: {e}")

        return leads[:max_results]

    def _parse_angellist_card(self, card) -> Optional[CollectedLead]:
        """Parse an AngelList/Wellfound startup card into a lead."""
        try:
            name_elem = card.select_one("h3, h4, a[class*='title'], span[class*='name']")
            name = name_elem.get_text(strip=True) if name_elem else ""

            link = card.select_one("a[href*='/company/'], a[href*='/startup/']")
            href = link.get("href", "") if link else ""

            desc_elem = card.select_one("p, div[class*='description'], span[class*='desc']")
            desc = desc_elem.get_text(strip=True) if desc_elem else ""

            location_elem = card.select_one("div[class*='location'], span[class*='location']")
            location = location_elem.get_text(strip=True) if location_elem else ""

            if not name:
                return None

            return CollectedLead(
                company_name=name[:255],
                company_url=f"https://wellfound.com{href}" if href else "",
                description=desc[:300] if desc else None,
                location_city=location,
                source="startup_directories",
                confidence=0.6,
            )
        except Exception:
            return None

    def _parse_yc_card(self, card) -> Optional[CollectedLead]:
        """Parse a Y Combinator company card into a lead."""
        try:
            name_elem = card.select_one("span, div[class*='name'], strong, b")
            name = name_elem.get_text(strip=True) if name_elem else ""

            link = card if card.name == "a" else card.select_one("a[href*='/companies/']")
            href = link.get("href", "") if link else ""

            desc_elem = card.select_one("p, div[class*='description']")
            desc = desc_elem.get_text(strip=True) if desc_elem else ""

            if not name:
                return None

            return CollectedLead(
                company_name=name[:255],
                company_url=f"https://www.ycombinator.com{href}" if href else "",
                description=desc[:300] if desc else None,
                source="startup_directories",
                confidence=0.7,
            )
        except Exception:
            return None