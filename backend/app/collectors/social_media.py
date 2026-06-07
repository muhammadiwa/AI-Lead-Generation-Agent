"""Social media monitor — discovers leads from Twitter/X, Reddit, Facebook.
Tracks mentions of topics relevant to B2B software development leads.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_json_api_headers, rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


class SocialMediaCollector(BaseCollector):
    """Monitor social media platforms for lead signals — companies hiring, 
    complaining about tech, or seeking development help.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "social_media"
        self._twitter_key = settings.twitter_api_key
        self._twitter_secret = settings.twitter_api_secret
        self._reddit_id = settings.reddit_client_id
        self._reddit_secret = settings.reddit_client_secret
        self._facebook_token = settings.facebook_access_token
        rate_limiter.register_source("twitter", rate=3.0, burst=5)
        rate_limiter.register_source("reddit", rate=2.0, burst=5)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        keywords = query.get(
            "keywords",
            [
                "looking for software developer",
                "need a CTO",
                "hiring engineering team",
                "tech stack migration",
                "digital transformation",
                "build MVP",
            ],
        )
        platforms = query.get("platforms", ["twitter", "reddit"])

        if "twitter" in platforms and self._twitter_key:
            twitter_leads = await self._search_twitter(keywords, max_results // 2)
            leads.extend(twitter_leads)

        if "reddit" in platforms:
            reddit_leads = await self._search_reddit(keywords, max_results // 2)
            leads.extend(reddit_leads)

        if "facebook" in platforms and self._facebook_token:
            fb_leads = await self._search_facebook(keywords, max_results // 3)
            leads.extend(fb_leads)

        return leads[:max_results]

    async def _search_twitter(self, keywords: List[str], max_results: int) -> List[CollectedLead]:
        """Search Twitter/X for relevant posts mentioning keywords."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for keyword in keywords[:5]:
                await rate_limiter.wait("twitter")
                await async_random_delay(2.0, 4.0)

                try:
                    resp = await client.get(
                        "https://api.twitter.com/2/tweets/search/recent",
                        headers={
                            "Authorization": f"Bearer {self._twitter_key}",
                            "Content-Type": "application/json",
                        },
                        params={
                            "query": f'({keyword}) -is:retweet lang:en',
                            "max_results": min(10, max_results),
                            "tweet.fields": "author_id,public_metrics,created_at",
                            "expansions": "author_id",
                            "user.fields": "name,username,description,location,url",
                        },
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

                        for tweet in data.get("data", []):
                            author = users.get(tweet.get("author_id"), {})
                            lead = CollectedLead(
                                company_name=author.get("name", ""),
                                company_url=author.get("url"),
                                company_domain=author.get("url"),
                                description=f"Tweet: {tweet.get('text', '')[:200]}",
                                source="social_media",
                                source_id=tweet.get("id"),
                                source_url=f"https://twitter.com/{author.get('username')}/status/{tweet.get('id')}",
                                confidence=0.5,
                            )
                            leads.append(lead)
                except Exception as e:
                    logger.warning(f"Twitter search failed for '{keyword}': {e}")

        return leads

    async def _search_reddit(self, keywords: List[str], max_results: int) -> List[CollectedLead]:
        """Search Reddit for posts in relevant subreddits."""
        leads: List[CollectedLead] = []
        subreddits = [
            "r/SaaS",
            "r/startups",
            "r/Entrepreneur",
            "r/webdev",
            "r/SoftwareEngineering",
            "r/techstartups",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Anonymous Reddit search — no auth needed for public data
            for keyword in keywords[:5]:
                await rate_limiter.wait("reddit")
                await async_random_delay(2.0, 3.0)

                try:
                    resp = await client.get(
                        "https://www.reddit.com/search.json",
                        headers={"User-Agent": "LeadGenAgent/1.0"},
                        params={
                            "q": keyword,
                            "sort": "new",
                            "limit": min(10, max_results),
                            "restrict_sr": False,
                        },
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        for post in data.get("data", {}).get("children", []):
                            post_data = post.get("data", {})
                            title = post_data.get("title", "")

                            lead = CollectedLead(
                                company_name=title.split("-")[0].split("|")[0].strip()[:255],
                                description=f"Reddit post: {title}\n{post_data.get('selftext', '')[:200]}",
                                source="social_media",
                                source_id=post_data.get("id"),
                                source_url=f"https://reddit.com{post_data.get('permalink', '')}",
                                confidence=0.5,
                            )
                            leads.append(lead)
                except Exception as e:
                    logger.warning(f"Reddit search failed for '{keyword}': {e}")

        return leads

    async def _search_facebook(self, keywords: List[str], max_results: int) -> List[CollectedLead]:
        """Search Facebook Graph API for relevant pages/groups."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for keyword in keywords[:3]:
                await async_random_delay(1.0, 2.0)

                try:
                    resp = await client.get(
                        "https://graph.facebook.com/v18.0/search",
                        params={
                            "q": keyword,
                            "type": "page",
                            "fields": "name,description,website,location",
                            "access_token": self._facebook_token,
                            "limit": min(10, max_results),
                        },
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        for page in data.get("data", []):
                            location = page.get("location", {})
                            lead = CollectedLead(
                                company_name=page.get("name", ""),
                                company_domain=page.get("website"),
                                company_url=page.get("website"),
                                description=page.get("description", ""),
                                location_city=location.get("city"),
                                location_country=location.get("country"),
                                source="social_media",
                                source_id=page.get("id"),
                                confidence=0.5,
                            )
                            leads.append(lead)
                except Exception as e:
                    logger.warning(f"Facebook search failed for '{keyword}': {e}")

        return leads