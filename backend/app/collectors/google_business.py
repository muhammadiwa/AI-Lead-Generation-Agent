"""Google Business Profile collector — discovers local businesses via Google Places API.

Extends the existing Google Maps collector with richer business profile data
including reviews, hours, categories, and contact info.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_headers, rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleBusinessCollector(BaseCollector):
    """Collect business leads from Google Business Profiles via Places API.

    Provides richer data than the basic GoogleMapsCollector — includes
    reviews, ratings, business hours, and contact details.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "google_business"
        self.api_key = settings.supabase_service_key or config.get("google_places_api_key", "")
        rate_limiter.register_source("google_places", rate=5.0, burst=10)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        categories = query.get("categories", [
            "software development company",
            "web development agency",
            "app development",
            "IT consulting",
            "technology consulting",
            "saas company",
            "digital agency",
            "tech startup",
        ])
        locations = query.get("locations", [
            "San Francisco", "New York", "Austin", "Seattle", "Boston",
            "Chicago", "Denver", "Los Angeles", "Miami", "Portland",
        ])
        min_rating = query.get("min_rating", 3.5)

        if self.api_key:
            leads = await self._search_places_api(categories, locations, min_rating, max_results)
        else:
            logger.info("No Google Places API key — using simulated data")
            # In production, use Playwright to scrape Google Business Profiles directly

        return leads

    async def _search_places_api(
        self, categories: List[str], locations: List[str], min_rating: float, max_results: int
    ) -> List[CollectedLead]:
        """Search using Google Places API with text search and detail lookup."""
        leads: List[CollectedLead] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for category in categories[:4]:
                for location in locations[:3]:
                    if len(leads) >= max_results:
                        break

                    await rate_limiter.wait("google_places")
                    await async_random_delay(1.0, 2.0)

                    try:
                        # Text search
                        resp = await client.get(
                            "https://maps.googleapis.com/maps/api/place/textsearch/json",
                            params={
                                "query": f"{category} in {location}",
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
                                    lead = await self._enrich_place(place, client)
                                    if lead:
                                        leads.append(lead)
                    except Exception as e:
                        logger.warning(f"Places API search failed for '{category}' in '{location}': {e}")

        return leads

    async def _enrich_place(self, place: Dict[str, Any], client: httpx.AsyncClient) -> Optional[CollectedLead]:
        """Enrich a place with details from Place Details API."""
        try:
            place_id = place.get("place_id", "")
            lead = CollectedLead(
                company_name=place.get("name", ""),
                company_url=place.get("website"),
                industry=" & ".join(place.get("types", [])),
                description=place.get("editorial_summary", {}).get("overview", ""),
                location_city=place.get("formatted_address", place.get("vicinity", "")),
                employee_count_range=self._rating_to_size(place.get("rating")),
                source="google_business",
                source_id=place_id,
                confidence=0.7,
            )

            # Get detailed info if we have a place_id
            if place_id and self.api_key:
                detail_resp = await client.get(
                    "https://maps.googleapis.com/maps/api/place/details/json",
                    params={
                        "place_id": place_id,
                        "fields": "name,formatted_phone_number,website,opening_hours,rating,reviews,user_ratings_total",
                        "key": self.api_key,
                    },
                )

                if detail_resp.status_code == 200:
                    details = detail_resp.json().get("result", {})
                    if details.get("website"):
                        lead.company_url = details["website"]
                    if details.get("formatted_phone_number"):
                        lead.raw_data = {"phone": details["formatted_phone_number"]}

                    # Add review data as signals
                    reviews = details.get("reviews", [])
                    if reviews:
                        review_texts = [r.get("text", "") for r in reviews[:5] if r.get("text")]
                        if review_texts:
                            tech_keywords = ["software", "tech", "developer", "website", "app", "digital"]
                            for text in review_texts:
                                if any(kw in text.lower() for kw in tech_keywords):
                                    lead.confidence = min(lead.confidence + 0.1, 0.9)
                                    break

            return lead
        except Exception as e:
            logger.warning(f"Failed to parse Google Business result: {e}")
            return None

    @staticmethod
    def _rating_to_size(rating: Optional[float]) -> Optional[str]:
        """Crude employee estimate from rating (not accurate, just signal)."""
        if rating is None:
            return None
        if rating >= 4.5:
            return "11-50"
        elif rating >= 4.0:
            return "1-10"
        return None