"""Crunchbase API collector — discovers companies by funding events and categories."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.utils import async_random_delay, build_json_api_headers, rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


class CrunchbaseCollector(BaseCollector):
    """Collect leads from Crunchbase — recent funding, company categories."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "crunchbase"
        self.api_key = settings.crunchbase_api_key
        self._base_url = "https://api.crunchbase.com/api/v4"
        rate_limiter.register_source("crunchbase", rate=4.0, burst=8)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        funding_rounds = query.get("funding_rounds", ["seed", "series_a", "series_b"])
        date_range_days = query.get("date_range_days", 90)

        if not self.api_key:
            logger.warning("No Crunchbase API key configured — returning empty results")
            return leads

        headers = build_json_api_headers(api_key=self.api_key)
        headers.update({
            "X-cb-user-key": self.api_key,
        })

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            for round_type in funding_rounds:
                await rate_limiter.wait("crunchbase")
                await async_random_delay(1.0, 2.0)

                try:
                    resp = await client.post(
                        f"{self._base_url}/searches/organizations",
                        json={
                            "field_ids": [
                                "identifier",
                                "name",
                                "website_url",
                                "short_description",
                                "location_identifiers",
                                "founded_on",
                                "employee_count",
                                "categories",
                                "total_funding",
                                "last_funding_type",
                                "funding_rounds",
                                "social_links",
                            ],
                            "query": [
                                {
                                    "type": "predicate",
                                    "field_id": "last_funding_type",
                                    "operator_id": "eq",
                                    "values": [round_type],
                                },
                                {
                                    "type": "predicate",
                                    "field_id": "updated_at",
                                    "operator_id": "gte",
                                    "values": [f"{date_range_days}_days_ago"],
                                },
                            ],
                            "limit": min(25, max_results),
                        },
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("entities", []):
                            if len(leads) >= max_results:
                                break
                            lead = self._parse_entity(item)
                            if lead:
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"Crunchbase search failed for round '{round_type}': {e}")

        return leads

    def _parse_entity(self, entity: Dict[str, Any]) -> Optional[CollectedLead]:
        """Parse a Crunchbase entity into a CollectedLead."""
        try:
            properties = entity.get("properties", {})
            funding_rounds_raw = properties.get("funding_rounds", [{}])
            total_funding = properties.get("total_funding", {}).get("value")

            lead = CollectedLead(
                company_name=properties.get("name", ""),
                company_domain=properties.get("website_url", {}).get("value"),
                company_url=properties.get("website_url", {}).get("value"),
                industry=properties.get("categories", [{}])[0].get("value") if properties.get("categories") else None,
                description=properties.get("short_description"),
                employee_count=properties.get("employee_count", {}).get("value"),
                employee_count_range=properties.get("employee_count", {}).get("value"),
                location_city=properties.get("location_identifiers", [{}])[0].get("city"),
                location_country=properties.get("location_identifiers", [{}])[0].get("country"),
                founded_year=properties.get("founded_on", {}).get("value"),
                funding_total=float(total_funding) if total_funding else None,
                funding_currency="USD",
                funding_rounds=[{"type": r.get("type"), "amount": r.get("money_raised", {}).get("value")} for r in funding_rounds_raw[:5]],
                source="crunchbase",
                source_id=str(entity.get("uuid", "")),
                source_url=f"https://www.crunchbase.com/organization/{properties.get('permalink', '')}",
                confidence=0.8,
            )

            return lead
        except Exception as e:
            logger.warning(f"Failed to parse Crunchbase entity: {e}")
            return None