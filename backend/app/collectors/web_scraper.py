"""Web scraper using Firecrawl API and Playwright for complex JS-heavy sites."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_headers, proxy_rotator, rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


class WebScraperCollector(BaseCollector):
    """General-purpose web scraper for job boards, tech news, and directories.

    Uses Firecrawl API as primary (AI-powered structured extraction) and falls back
    to Playwright/httpx + BeautifulSoup for direct scraping.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "web_scrape"
        self.firecrawl_key = settings.firecrawl_api_key
        self._firecrawl_url = "https://api.firecrawl.dev/v1"
        rate_limiter.register_source("web_scrape", rate=5.0, burst=10)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        urls = query.get("urls", [])
        scrape_type = query.get("scrape_type", "job_boards")  # job_boards, tech_news, directories

        if urls:
            # Direct URL scraping
            for url in urls[:10]:
                if len(leads) >= max_results:
                    break
                await rate_limiter.wait("web_scrape")
                lead = await self._scrape_url(url)
                if lead:
                    leads.append(lead)
        elif self.firecrawl_key:
            # Use Firecrawl for intelligent crawling
            leads = await self._firecrawl_search(scrape_type, max_results)
        else:
            logger.info("No Firecrawl key — using direct HTTP scraping")
            leads = await self._direct_scrape(scrape_type, max_results)

        return leads

    async def _firecrawl_search(self, scrape_type: str, max_results: int) -> List[CollectedLead]:
        """Use Firecrawl API for AI-powered web scraping."""
        leads: List[CollectedLead] = []

        # Define seed URLs based on scrape type
        seed_urls = self._get_seed_urls(scrape_type)

        async with httpx.AsyncClient(timeout=60.0) as client:
            for url in seed_urls[:3]:
                await rate_limiter.wait("web_scrape")

                try:
                    resp = await client.post(
                        f"{self._firecrawl_url}/crawl",
                        headers={"Authorization": f"Bearer {self.firecrawl_key}"},
                        json={
                            "url": url,
                            "pageOptions": {"onlyMainContent": True},
                            "crawlerOptions": {"maxDepth": 1, "limit": min(5, max_results)},
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for page in data.get("data", []):
                            lead = self._parse_firecrawl_page(page)
                            if lead:
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"Firecrawl crawl failed for {url}: {e}")

        return leads

    async def _direct_scrape(self, scrape_type: str, max_results: int) -> List[CollectedLead]:
        """Direct HTTP scraping using httpx + BeautifulSoup."""
        leads: List[CollectedLead] = []
        seed_urls = self._get_seed_urls(scrape_type)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for url in seed_urls[:5]:
                await rate_limiter.wait("web_scrape")
                await async_random_delay(2.0, 4.0)

                try:
                    proxy = proxy_rotator.random()
                    resp = await client.get(
                        url,
                        headers=build_headers(),
                        proxies=proxy,
                    )

                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        # Extract company names, URLs from common patterns
                        for link in soup.find_all("a", href=True):
                            text = link.get_text(strip=True)
                            href = link["href"]
                            if text and len(text) > 3 and "company" in href.lower():
                                lead = CollectedLead(
                                    company_name=text,
                                    company_url=href if href.startswith("http") else None,
                                    source="web_scrape",
                                    source_url=url,
                                    confidence=0.4,
                                )
                                leads.append(lead)
                                if len(leads) >= max_results:
                                    break
                except Exception as e:
                    logger.warning(f"Direct scrape failed for {url}: {e}")

        return leads

    async def _scrape_url(self, url: str) -> Optional[CollectedLead]:
        """Scrape a single URL for company information."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers=build_headers(referer=url))
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")

                    title = soup.find("title")
                    description = soup.find("meta", attrs={"name": "description"})

                    return CollectedLead(
                        company_name=title.get_text(strip=True) if title else url,
                        company_url=url,
                        description=description.get("content") if description else None,
                        tech_stack=self._detect_tech_stack(soup),
                        source="web_scrape",
                        source_url=url,
                        confidence=0.5,
                    )
            except Exception as e:
                logger.warning(f"URL scrape failed for {url}: {e}")
        return None

    def _detect_tech_stack(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Detect technologies from HTML elements."""
        techs = []
        # Common tech indicators
        if soup.find("script", src=lambda s: s and "react" in s.lower()):
            techs.append("React")
        if soup.find("script", src=lambda s: s and "vue" in s.lower()):
            techs.append("Vue.js")
        if soup.find("script", src=lambda s: s and "angular" in s.lower()):
            techs.append("Angular")
        if soup.find("script", src=lambda s: s and "next" in s.lower()):
            techs.append("Next.js")
        if soup.find("meta", attrs={"name": "generator", "content": lambda c: c and "wordpress" in c.lower()}):
            techs.append("WordPress")

        return {"detected_technologies": techs} if techs else None

    def _get_seed_urls(self, scrape_type: str) -> List[str]:
        """Get seed URLs based on scrape type."""
        urls = {
            "job_boards": [
                "https://news.ycombinator.com/jobs",
                "https://remoteok.com",
                "https://weworkremotely.com",
            ],
            "tech_news": [
                "https://techcrunch.com",
                "https://www.theverge.com/tech",
                "https://news.ycombinator.com",
            ],
            "directories": [
                "https://www.producthunt.com",
                "https://www.ycombinator.com/companies",
                "https://www.saas1000.com",
            ],
        }
        return urls.get(scrape_type, urls["job_boards"])

    def _parse_firecrawl_page(self, page: Dict[str, Any]) -> Optional[CollectedLead]:
        """Parse a Firecrawl response page into a lead."""
        try:
            metadata = page.get("metadata", {})
            return CollectedLead(
                company_name=metadata.get("title", "").split(" - ")[0].split(" | ")[0],
                company_url=metadata.get("sourceURL"),
                description=metadata.get("description"),
                source="web_scrape",
                source_url=metadata.get("sourceURL"),
                confidence=0.6,
            )
        except Exception:
            return None