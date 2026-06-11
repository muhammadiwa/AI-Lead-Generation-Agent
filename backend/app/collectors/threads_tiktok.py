"""Threads & TikTok social monitoring collector.

Uses web scraping/API simulation for Threads (Instagram Threads) and TikTok
to find posts about needing developers, software help, automation, etc.
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


LEAD_KEYWORDS = [
    "need a developer",
    "looking for dev team",
    "help with software",
    "build my app",
    "need a cto",
    "software agency",
    "web development help",
    "automate my business",
    "tech cofounder",
    "build a platform",
    "mvp development",
    "software outsourcing",
    "need engineering team",
]


class ThreadsTikTokCollector(BaseCollector):
    """Collect leads by monitoring Threads and TikTok for lead signals."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "social_platforms"
        rate_limiter.register_source("threads", rate=2.0, burst=3)
        rate_limiter.register_source("tiktok", rate=1.0, burst=2)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        keywords = query.get("keywords", LEAD_KEYWORDS[:5])
        platforms = query.get("platforms", ["threads", "tiktok"])

        if "threads" in platforms:
            for kw in keywords[:3]:
                if len(leads) >= max_results:
                    break
                thr_leads = await self._search_threads(kw, max_results // 6)
                leads.extend(thr_leads)

        if "tiktok" in platforms:
            for kw in keywords[:3]:
                if len(leads) >= max_results:
                    break
                tt_leads = await self._search_tiktok(kw, max_results // 6)
                leads.extend(tt_leads)

        return leads[:max_results]

    async def _search_threads(self, keyword: str, max_results: int) -> List[CollectedLead]:
        """Search Threads for posts matching keyword."""
        leads: List[CollectedLead] = []
        await rate_limiter.wait("threads", 1)
        await async_random_delay(3.0, 6.0)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                proxy = proxy_rotator.random()
                resp = await client.get(
                    f"https://www.threads.net/search?q={quote_plus(keyword)}",
                    headers=build_headers(referer="https://www.threads.net"),
                    proxies=proxy,
                )

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    leads = self._parse_threads_page(soup, keyword, max_results)
                else:
                    logger.info(f"Threads returned {resp.status_code} for '{keyword}'")
            except Exception as e:
                logger.warning(f"Threads search failed for '{keyword}': {e}")

        return leads

    async def _search_tiktok(self, keyword: str, max_results: int) -> List[CollectedLead]:
        """Search TikTok for posts matching keyword."""
        leads: List[CollectedLead] = []
        await rate_limiter.wait("tiktok", 1)
        await async_random_delay(4.0, 8.0)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                proxy = proxy_rotator.random()
                resp = await client.get(
                    f"https://www.tiktok.com/search?q={quote_plus(keyword)}",
                    headers=build_headers(referer="https://www.tiktok.com"),
                    proxies=proxy,
                )

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    leads = self._parse_tiktok_page(soup, keyword, max_results)
                else:
                    logger.info(f"TikTok returned {resp.status_code} for '{keyword}'")
            except Exception as e:
                logger.warning(f"TikTok search failed for '{keyword}': {e}")

        return leads

    def _parse_threads_page(self, soup: BeautifulSoup, keyword: str, max_results: int) -> List[CollectedLead]:
        """Parse Threads search results for leads."""
        leads: List[CollectedLead] = []

        # Look for post content and user info in the page
        for post in soup.select("article, div[role='article'], div[data-pressable-container]")[:20]:
            try:
                text_elems = post.find_all(["p", "span", "div"], text=True)
                post_text = " ".join(e.get_text(strip=True) for e in text_elems if len(e.get_text(strip=True)) > 20)

                if not post_text or len(post_text) < 20:
                    continue

                user_elem = post.select_one("a[href*='/profile/'], a[href^='/']")
                username = user_elem.get_text(strip=True) if user_elem else ""
                user_link = user_elem.get("href", "") if user_elem else ""

                company_name = self._extract_company(post_text) or username or "Unknown"
                lead = CollectedLead(
                    company_name=company_name[:255],
                    description=f"Threads post: {post_text[:300]}",
                    source="social_platforms",
                    source_url=f"https://www.threads.net{user_link}" if user_link else "",
                    confidence=0.4,
                    raw_data={"keyword": keyword, "platform": "threads"},
                )
                leads.append(lead)
            except Exception:
                continue

        return leads[:max_results]

    def _parse_tiktok_page(self, soup: BeautifulSoup, keyword: str, max_results: int) -> List[CollectedLead]:
        """Parse TikTok search results for leads."""
        leads: List[CollectedLead] = []

        for result in soup.select("div[data-e2e='search-result-item'], div[class*='search-item'], div[class*='video-card']")[:20]:
            try:
                text_elems = result.find_all(["p", "span", "h3", "div"], text=True)
                post_text = " ".join(e.get_text(strip=True) for e in text_elems if len(e.get_text(strip=True)) > 15)

                if not post_text or len(post_text) < 15:
                    continue

                link = result.select_one("a[href*='/video/'], a[href*='/@']")
                href = link.get("href", "") if link else ""
                username = ""
                if link:
                    user_match = re.search(r'/@([^/]+)', href)
                    if user_match:
                        username = user_match.group(1)

                company_name = self._extract_company(post_text) or username or "Unknown"
                lead = CollectedLead(
                    company_name=company_name[:255],
                    description=f"TikTok post: {post_text[:300]}",
                    source="social_platforms",
                    source_url=f"https://www.tiktok.com{href}" if href else "",
                    confidence=0.4,
                    raw_data={"keyword": keyword, "platform": "tiktok"},
                )
                leads.append(lead)
            except Exception:
                continue

        return leads[:max_results]

    def _extract_company(self, text: str) -> Optional[str]:
        """Extract company or username from text."""
        patterns = [
            re.compile(r'(?:my\s+company\s+is\s+|at\s+)([A-Z][A-Za-z0-9\s&]+?)(?:\s+(?:is|are|has|\.|,|!))'),
            re.compile(r'(?:I\s+(?:run|own|work\s+at|started|built)\s+)([A-Z][A-Za-z0-9\s&]+?)(?:\s+(?:and|\.|,|!|$))'),
        ]
        for pat in patterns:
            match = pat.search(text)
            if match:
                name = match.group(1).strip()
                if 2 < len(name) < 80:
                    return name
        return None