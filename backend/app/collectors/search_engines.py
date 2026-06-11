"""Google & Bing Search Engine collector — monitors SERP for lead signals.

Searches for queries like "looking for developer", "need software agency",
"hiring CTO", etc. and extracts company names, URLs, and context.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_headers, rate_limiter, proxy_rotator

logger = logging.getLogger(__name__)


# Lead-signal search queries
LEAD_QUERIES = [
    "looking for software developer",
    "need a software agency",
    "hiring CTO",
    "looking for development team",
    "need to build an app",
    "seeking web development services",
    "looking for tech co-founder",
    "need help with software project",
    "hiring remote developers",
    "outsourcing software development",
    "need a technical co-founder",
    "looking for react developers",
    "hiring full stack developer",
    "need MVP built",
    "looking for python developers",
    "digital transformation agency",
    "need to modernize tech stack",
    "seeking engineering team",
]


class GoogleBingCollector(BaseCollector):
    """Collect leads by searching Google and Bing for lead-signal queries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "search_engines"
        rate_limiter.register_source("google", rate=2.0, burst=3)
        rate_limiter.register_source("bing", rate=3.0, burst=5)

        # Company name extraction patterns
        self._company_patterns = [
            re.compile(r'([A-Z][A-Za-z0-9]+(?:\.(?:com|io|ai|app|dev|tech|co))?)'),
            re.compile(r'(?:(?:at|with|from)\s+)([A-Z][A-Za-z0-9\s&]+?)(?:\s+(?:is|are|has|was|we|they|\.|,|!|\?))'),
        ]

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        search_queries = query.get("queries", LEAD_QUERIES[:5])
        engines = query.get("engines", ["google", "bing"])
        max_per_engine = max_results // (len(engines) * min(len(search_queries), 5))

        for search_query in search_queries[:5]:
            if len(leads) >= max_results:
                break

            if "google" in engines:
                google_leads = await self._search_google(search_query, max_per_engine)
                leads.extend(google_leads)

            if "bing" in engines:
                bing_leads = await self._search_bing(search_query, max_per_engine)
                leads.extend(bing_leads)

        # Deduplicate by URL
        seen_urls = set()
        unique_leads = []
        for lead in leads:
            key = lead.company_url or lead.company_name
            if key and key not in seen_urls:
                seen_urls.add(key)
                unique_leads.append(lead)

        return unique_leads[:max_results]

    async def _search_google(self, search_query: str, max_results: int) -> List[CollectedLead]:
        """Search Google via scraping (with anti-blocking)."""
        leads: List[CollectedLead] = []
        await rate_limiter.wait("google", 1)
        await async_random_delay(3.0, 6.0)

        url = f"https://www.google.com/search?q={quote_plus(search_query)}&hl=en&num={min(max_results, 10)}"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                proxy = proxy_rotator.random()
                resp = await client.get(
                    url,
                    headers=build_headers(referer="https://www.google.com"),
                    proxies=proxy,
                )

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    results = self._parse_google_results(soup, search_query)
                    leads.extend(results[:max_results])
                else:
                    logger.warning(f"Google search returned {resp.status_code}")
            except Exception as e:
                logger.warning(f"Google search failed for '{search_query}': {e}")

        return leads

    async def _search_bing(self, search_query: str, max_results: int) -> List[CollectedLead]:
        """Search Bing via scraping."""
        leads: List[CollectedLead] = []
        await rate_limiter.wait("bing", 1)
        await async_random_delay(2.0, 4.0)

        url = f"https://www.bing.com/search?q={quote_plus(search_query)}&count={min(max_results, 10)}"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                proxy = proxy_rotator.random()
                resp = await client.get(
                    url,
                    headers=build_headers(referer="https://www.bing.com"),
                    proxies=proxy,
                )

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    results = self._parse_bing_results(soup, search_query)
                    leads.extend(results[:max_results])
                else:
                    logger.warning(f"Bing search returned {resp.status_code}")
            except Exception as e:
                logger.warning(f"Bing search failed for '{search_query}': {e}")

        return leads

    def _parse_google_results(self, soup: BeautifulSoup, search_query: str) -> List[CollectedLead]:
        """Parse Google search results page."""
        leads: List[CollectedLead] = []

        # Google result containers
        result_divs = soup.select("div.g, div[data-hveid], div[data-sokoban-container]")

        for div in result_divs[:15]:
            try:
                link = div.select_one("a[href^='http']")
                if not link:
                    continue

                href = link.get("href", "")
                # Skip Google internal links
                if not href or "google.com" in href or "googleusercontent" in href:
                    continue

                title_elem = div.select_one("h3, a > span, .DKV0Md")
                title = title_elem.get_text(strip=True) if title_elem else ""

                snippet_elem = div.select_one(".VwiC3b, .lEBKkf, span.aCOpRe, .st")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if not title and not snippet:
                    continue

                company_name = self._extract_company_name(title, snippet)
                domain = self._extract_domain(href)

                lead = CollectedLead(
                    company_name=company_name or title.split(" - ")[0].split(" | ")[0][:255],
                    company_domain=domain,
                    company_url=href,
                    description=f"Search context: {snippet[:300]}" if snippet else title[:300],
                    source="search_engines",
                    source_url=href,
                    confidence=0.5,
                    raw_data={"search_query": search_query, "engine": "google", "title": title},
                )
                leads.append(lead)
            except Exception:
                continue

        return leads

    def _parse_bing_results(self, soup: BeautifulSoup, search_query: str) -> List[CollectedLead]:
        """Parse Bing search results page."""
        leads: List[CollectedLead] = []

        for result in soup.select("li.b_algo, .b_algo")[:15]:
            try:
                link = result.select_one("a[href^='http']")
                if not link:
                    continue

                href = link.get("href", "")
                title_elem = result.select_one("h2 a, h2")
                title = title_elem.get_text(strip=True) if title_elem else ""

                snippet_elem = result.select_one(".b_caption p, .b_lineclamp2, .b_caption")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if not title and not snippet:
                    continue

                company_name = self._extract_company_name(title, snippet)
                domain = self._extract_domain(href)

                lead = CollectedLead(
                    company_name=company_name or title.split(" - ")[0].split(" | ")[0][:255],
                    company_domain=domain,
                    company_url=href,
                    description=f"Search context: {snippet[:300]}" if snippet else title[:300],
                    source="search_engines",
                    source_url=href,
                    confidence=0.5,
                    raw_data={"search_query": search_query, "engine": "bing", "title": title},
                )
                leads.append(lead)
            except Exception:
                continue

        return leads

    def _extract_company_name(self, title: str, snippet: str) -> Optional[str]:
        """Extract a company name from search result text."""
        text = f"{title} {snippet}"

        # Try to find company-like names
        for pattern in self._company_patterns:
            match = pattern.search(text)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and len(name) < 100:
                    return name
        return None

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from a URL."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split("/")[0]
            if domain and "." in domain:
                return domain
        except Exception:
            pass
        return None