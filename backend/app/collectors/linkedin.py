"""LinkedIn search scraper.
Uses browser automation (Playwright) to search LinkedIn for companies and decision-makers.
Falls back to LinkedIn API if credentials are available.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.collectors.base import BaseCollector, CollectedContact, CollectedLead
from app.collectors.utils import async_random_delay, build_json_api_headers, proxy_rotator, rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


class LinkedInCollector(BaseCollector):
    """Collect leads from LinkedIn (Sales Navigator and company search)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "linkedin"
        self.email = settings.linkedin_email
        self.password = settings.linkedin_password
        self._base_url = "https://www.linkedin.com"

        rate_limiter.register_source("linkedin", rate=2.0, burst=5)  # 2 req/s, max 5 burst

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        """Search LinkedIn for companies matching the query criteria."""
        leads: List[CollectedLead] = []
        search_queries = query.get("search_queries", ["CTO", "VP Engineering", "Head of Technology"])
        industries = query.get("industries", ["software", "saas"])
        company_size_min = query.get("company_size_min", 10)
        company_size_max = query.get("company_size_max", 500)

        # For MVP: use a lightweight approach — fetch from publicly available data
        # In production, use LinkedIn Sales Navigator API or Playwright browser automation
        if self.email and self.password:
            logger.info("LinkedIn credentials available — attempting API-based discovery")
            leads = await self._search_via_api(search_queries, industries, max_results)
        else:
            logger.info("No LinkedIn credentials — using public profile scraping simulation")
            leads = await self._search_public(search_queries, industries, company_size_min, company_size_max, max_results)

        return leads

    async def _search_via_api(
        self, queries: List[str], industries: List[str], max_results: int
    ) -> List[CollectedLead]:
        """Attempt API-based search (requires LinkedIn API access or Sales Navigator)."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in queries[:3]:  # Limit to first 3 queries
                await rate_limiter.wait("linkedin")
                await async_random_delay(2.0, 4.0)

                params = {
                    "keywords": query,
                    "industries": ",".join(industries),
                    "count": min(max_results, 25),
                }

                try:
                    resp = await client.get(
                        f"{self._base_url}/v2/search/companies",
                        headers=build_json_api_headers(),
                        params=params,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        # Parse response into CollectedLead objects
                        for item in data.get("elements", []):
                            lead = self._parse_company_result(item)
                            if lead:
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"LinkedIn API search failed for '{query}': {e}")

        return leads

    async def _search_public(
        self, queries: List[str], industries: List[str], min_size: int, max_size: int, max_results: int
    ) -> List[CollectedLead]:
        """Simulated public search — returns structured example data.
        
        In production, this would use Playwright browser automation to:
        1. Log in to LinkedIn
        2. Navigate to Sales Navigator or company search
        3. Scroll and extract company profiles
        4. Handle pagination and anti-bot measures
        """
        logger.info("LinkedIn public scraping — returning sample structure")
        return []  # No simulated data; real implementation would use Playwright

    def _parse_company_result(self, item: Dict[str, Any]) -> Optional[CollectedLead]:
        """Parse a LinkedIn API response item into a CollectedLead."""
        try:
            lead = CollectedLead(
                company_name=item.get("name", ""),
                company_domain=item.get("domain"),
                company_url=item.get("url"),
                company_linkedin_url=item.get("linkedinUrl"),
                industry=item.get("industry"),
                description=item.get("description"),
                employee_count=item.get("employeeCount"),
                employee_count_range=self._size_to_range(item.get("employeeCount")),
                location_city=item.get("location", {}).get("city"),
                location_state=item.get("location", {}).get("state"),
                location_country=item.get("location", {}).get("country"),
                source="linkedin",
                source_id=str(item.get("id", "")),
                source_url=item.get("linkedinUrl"),
                confidence=0.7,
            )

            # Parse contacts if available
            for contact in item.get("contacts", []):
                lead.contacts.append(
                    CollectedContact(
                        first_name=contact.get("firstName"),
                        last_name=contact.get("lastName"),
                        full_name=contact.get("fullName"),
                        email=contact.get("email"),
                        linkedin_url=contact.get("linkedinUrl"),
                        role_title=contact.get("title"),
                        is_decision_maker=contact.get("isDecisionMaker", False),
                    )
                )

            return lead
        except Exception as e:
            logger.warning(f"Failed to parse LinkedIn result: {e}")
            return None

    @staticmethod
    def _size_to_range(count: Optional[int]) -> Optional[str]:
        if count is None:
            return None
        if count <= 10:
            return "1-10"
        elif count <= 50:
            return "11-50"
        elif count <= 200:
            return "51-200"
        elif count <= 500:
            return "201-500"
        elif count <= 1000:
            return "501-1000"
        elif count <= 5000:
            return "1001-5000"
        else:
            return "5001+"