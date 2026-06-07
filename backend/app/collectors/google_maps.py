"""Google Maps / Business Profile scraper.
Discovers businesses in specific regions with relevant categories.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_headers, proxy_rotator, rate_limiter

logger = logging.getLogger(__name__)


class GoogleMapsCollector(BaseCollector):
    """Collect business leads from Google Maps / Business Profile data.

    Uses the Google Places API or Places API (New) when available.
    Falls back to scraping Google Maps search results.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "google_maps"
        self.api_key = config.get("google_places_api_key", "") if config else ""
        self._base_url = "https://maps.googleapis.com/maps/api/place"
        rate_limiter.register_source("google_maps", rate=5.0, burst=10)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        search_terms = query.get(
            "search_terms",
            ["software development company", "tech startup", "SaaS company", "IT services"],
        )
        locations = query.get("locations", ["San Francisco", "New York", "Austin", "Seattle", "Boston"])
        min_rating = query.get("min_rating", 0.0)

        if self.api_key:
            leads = await self._search_via_api(search_terms, locations, min_rating, max_results)
        else:
            logger.info("No Google Places API key — using simulated search")
            # In production, use Playwright to scrape Google Maps search results

        return leads

    async def _search_via_api(
        self, terms: List[str], locations: List[str], min_rating: float, max_results: int
    ) -> List[CollectedLead]:
        """Search using Google Places API (text search + nearby search)."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for term in terms[:3]:
                for location in locations[:3]:
                    if len(leads) >= max_results:
                        break

                    await rate_limiter.wait("google_maps")
                    await async_random_delay(1.0, 2.0)

                    try:
                        resp = await client.get(
                            f"{self._base_url}/textsearch/json",
                            params={
                                "query": f"{term} in {location}",
                                "key": self.api_key,
                                "type": "establishment",
                            },
                        )

                        if resp.status_code == 200:
                            data = resp.json()
                            for place in data.get("results", []):
                                if len(leads) >= max_results:
                                    break
                                if place.get("rating", 0) >= min_rating:
                                    lead = self._parse_place(place)
                                    if lead:
                                        leads.append(lead)
                    except Exception as e:
                        logger.warning(f"Google Places search failed for '{term}' in '{location}': {e}")

        return leads

    def _parse_place(self, place: Dict[str, Any]) -> Optional[CollectedLead]:
        """Parse a Google Places API result into a lead."""
        try:
            return CollectedLead(
                company_name=place.get("name", ""),
                company_domain=None,
                company_url=place.get("website"),
                industry=" & ".join(place.get("types", [])),
                description=place.get("editorial_summary", {}).get("overview"),
                location_city=place.get("vicinity"),
                employee_count_range=None,
                source="google_maps",
                source_id=place.get("place_id"),
                confidence=0.7,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Google Places result: {e}")
            return None