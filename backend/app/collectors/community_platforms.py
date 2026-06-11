"""Discord, Slack & Telegram Groups collector.

Monitors public channels/groups for lead signals — companies seeking 
development help, hiring engineers, or discussing tech problems.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_headers, proxy_rotator, rate_limiter

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "looking for developer",
    "need help with code",
    "software development agency",
    "hire react developer",
    "need a technical team",
    "build my saas",
    "automation consulting",
    "help with tech stack",
    "web development services",
    "looking for engineering help",
    "need a development partner",
    "custom software quote",
]


class CommunityCollector(BaseCollector):
    """Collect leads from public Discord servers, Slack groups, and Telegram channels."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "community_platforms"
        rate_limiter.register_source("disboard", rate=2.0, burst=3)
        rate_limiter.register_source("telegram", rate=2.0, burst=3)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        platforms = query.get("platforms", ["disboard", "telegram"])
        keywords = query.get("keywords", SEARCH_QUERIES[:5])

        if "disboard" in platforms:
            for kw in keywords[:3]:
                if len(leads) >= max_results:
                    break
                dis_leads = await self._search_disboard(kw, max_results // 6)
                leads.extend(dis_leads)

        if "telegram" in platforms:
            for kw in keywords[:3]:
                if len(leads) >= max_results:
                    break
                tg_leads = await self._search_telegram(kw, max_results // 6)
                leads.extend(tg_leads)

        return leads[:max_results]

    async def _search_disboard(self, keyword: str, max_results: int) -> List[CollectedLead]:
        """Search Disboard (Discord server directory) for relevant servers."""
        leads: List[CollectedLead] = []
        await rate_limiter.wait("disboard")
        await async_random_delay(2.0, 4.0)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                proxy = proxy_rotator.random()
                resp = await client.get(
                    "https://disboard.org/search",
                    params={"keyword": keyword},
                    headers=build_headers(referer="https://disboard.org"),
                    proxies=proxy,
                )
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    for card in soup.select("div[class*='server-card'], div[class*='card']")[:15]:
                        lead = self._parse_disboard_card(card, keyword)
                        if lead:
                            leads.append(lead)
            except Exception as e:
                logger.warning(f"Disboard search failed for '{keyword}': {e}")
        return leads[:max_results]

    async def _search_telegram(self, keyword: str, max_results: int) -> List[CollectedLead]:
        """Search Telegram via public channel search."""
        leads: List[CollectedLead] = []
        await rate_limiter.wait("telegram")
        await async_random_delay(2.0, 4.0)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                proxy = proxy_rotator.random()
                resp = await client.get(
                    "https://t.me/s/",
                    params={"q": keyword},
                    headers=build_headers(referer="https://t.me"),
                    proxies=proxy,
                )
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    for result in soup.select("div[class*='message'], div[class*='tgme_widget_message_wrap']")[:20]:
                        lead = self._parse_telegram_post(result, keyword)
                        if lead:
                            leads.append(lead)
            except Exception as e:
                logger.warning(f"Telegram search failed for '{keyword}': {e}")
        return leads[:max_results]

    def _parse_disboard_card(self, card, keyword: str) -> Optional[CollectedLead]:
        try:
            name_elem = card.select_one("h3, h2, a[class*='title']")
            name = name_elem.get_text(strip=True) if name_elem else ""
            desc_elem = card.select_one("p, div[class*='description']")
            desc = desc_elem.get_text(strip=True) if desc_elem else ""
            if not name:
                return None
            company_name = name
            for suffix in [" Discord", " Server", " Community", " HQ"]:
                if company_name.endswith(suffix):
                    company_name = company_name[: -len(suffix)]
            return CollectedLead(
                company_name=company_name[:255],
                description=f"Discord community: {desc[:200]}" if desc else f"Discord: {keyword}",
                source="community_platforms", confidence=0.4,
                raw_data={"keyword": keyword, "platform": "discord"},
            )
        except Exception:
            return None

    def _parse_telegram_post(self, post, keyword: str) -> Optional[CollectedLead]:
        try:
            text_elem = post.select_one("div[class*='text'], p, span[class*='text']")
            text = text_elem.get_text(strip=True) if text_elem else ""
            if not text or len(text) < 30:
                return None
            sender_elem = post.select_one("a[class*='sender'], div[class*='author']")
            sender = sender_elem.get_text(strip=True) if sender_elem else ""
            company_name = self._extract_company(text) or sender or "Telegram User"
            return CollectedLead(
                company_name=company_name[:255],
                description=f"Telegram: {text[:500]}",
                source="community_platforms", confidence=0.4,
                raw_data={"keyword": keyword, "platform": "telegram", "sender": sender},
            )
        except Exception:
            return None

    def _extract_company(self, text: str) -> Optional[str]:
        patterns = [
            re.compile(r'(?:my\s+(?:company|startup|business)\s+(?:is\s+)?)([A-Z][A-Za-z0-9\s&]+?)(?:\s+(?:is|are|\.|,))'),
            re.compile(r'(?:I\s+(?:run|own|work\s+(?:at|for)|started|built)\s+)([A-Z][A-Za-z0-9\s&]+?)(?:\s+(?:and|\.|,|!|$))'),
        ]
        for pat in patterns:
            match = pat.search(text)
            if match:
                name = match.group(1).strip()
                if 2 < len(name) < 80:
                    return name
        return None