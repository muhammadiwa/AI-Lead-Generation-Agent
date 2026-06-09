"""Company enrichment service — fetches additional data from Clearbit, Hunter, Crunchbase."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from app.collectors.utils import async_random_delay, rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """Result of enriching a lead with external data."""
    domain: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    revenue_range: Optional[str] = None
    funding_total: Optional[float] = None
    tech_stack: List[str] = field(default_factory=list)
    social_links: Dict[str, str] = field(default_factory=dict)
    contacts: List[Dict[str, Any]] = field(default_factory=list)
    description: Optional[str] = None
    location: Optional[str] = None
    founded_year: Optional[int] = None
    confidence: float = 0.0


class EnrichmentService:
    """Enrich lead data from multiple external APIs."""

    def __init__(self):
        self.clearbit_key = settings.clearbit_api_key
        self.hunter_key = settings.hunter_api_key
        self.crunchbase_key = settings.crunchbase_api_key

    async def enrich(self, company_domain: str, company_name: str = "") -> EnrichmentResult:
        """Enrich a lead using all available data sources."""
        result = EnrichmentResult(domain=company_domain)

        if self.clearbit_key and company_domain:
            clearbit_data = await self._enrich_clearbit(company_domain)
            if clearbit_data:
                result = self._merge(result, clearbit_data)

        if self.hunter_key and company_domain:
            hunter_contacts = await self._find_contacts(company_domain)
            if hunter_contacts:
                result.contacts.extend(hunter_contacts)

        if self.crunchbase_key and company_name:
            cb_data = await self._enrich_crunchbase(company_name)
            if cb_data:
                result = self._merge(result, cb_data)

        return result

    async def enrich_bulk(self, leads: List[Dict[str, Any]]) -> List[EnrichmentResult]:
        """Enrich multiple leads in batch."""
        results = []
        for lead in leads:
            domain = lead.get("company_domain", "") or ""
            name = lead.get("company_name", "")
            if domain:
                result = await self.enrich(domain, name)
                results.append(result)
                await async_random_delay(0.5, 1.5)
            else:
                results.append(EnrichmentResult(domain=domain))
        return results

    async def _enrich_clearbit(self, domain: str) -> Optional[Dict[str, Any]]:
        """Fetch company data from Clearbit Reveal API."""
        await rate_limiter.wait("clearbit", 1)

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(
                    f"https://company.clearbit.com/v2/companies/find?domain={domain}",
                    headers={"Authorization": f"Bearer {self.clearbit_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "company_name": data.get("name"),
                        "industry": data.get("industry"),
                        "employee_count": data.get("metrics", {}).get("employees"),
                        "employee_range": data.get("metrics", {}).get("employeesRange"),
                        "revenue_range": data.get("metrics", {}).get("estimatedAnnualRevenue"),
                        "description": data.get("description"),
                        "location": data.get("location"),
                        "founded_year": data.get("foundedYear"),
                        "tech_stack": [t.get("name") for t in (data.get("tech", []) or [])],
                        "social_links": {
                            "linkedin": data.get("linkedin", {}).get("handle", ""),
                            "twitter": data.get("twitter", {}).get("handle", ""),
                            "facebook": data.get("facebook", {}).get("handle", ""),
                            "crunchbase": data.get("crunchbase", {}).get("handle", ""),
                        },
                        "funding_total": data.get("metrics", {}).get("raised"),
                        "confidence": 0.8,
                    }
                elif resp.status_code == 404:
                    logger.info(f"Clearbit: no data for {domain}")
                else:
                    logger.warning(f"Clearbit error {resp.status_code} for {domain}")
            except Exception as e:
                logger.warning(f"Clearbit enrichment failed for {domain}: {e}")
        return None

    async def _find_contacts(self, domain: str) -> List[Dict[str, Any]]:
        """Find contact emails via Hunter.io API."""
        await rate_limiter.wait("hunter", 1)

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={"domain": domain, "api_key": self.hunter_key},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    contacts = []
                    for email_data in (data.get("emails") or []):
                        contacts.append({
                            "first_name": email_data.get("first_name", ""),
                            "last_name": email_data.get("last_name", ""),
                            "email": email_data.get("value", ""),
                            "role": email_data.get("position", ""),
                            "seniority": email_data.get("seniority", ""),
                            "department": email_data.get("department", ""),
                            "confidence": email_data.get("confidence", 0),
                        })
                    return contacts
            except Exception as e:
                logger.warning(f"Hunter enrichment failed for {domain}: {e}")
        return []

    async def _enrich_crunchbase(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Fetch Crunchbase data for a company."""
        await rate_limiter.wait("crunchbase", 1)

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(
                    "https://api.crunchbase.com/api/v4/searches/organizations",
                    headers={"X-cb-user-key": self.crunchbase_key},
                    json={
                        "field_ids": ["name", "short_description", "total_funding", "employee_count", "founded_on"],
                        "query": [{
                            "type": "predicate",
                            "field_id": "name",
                            "operator_id": "eq",
                            "values": [company_name],
                        }],
                        "limit": 1,
                    },
                )
                if resp.status_code == 200:
                    entities = resp.json().get("entities", [])
                    if entities:
                        props = entities[0].get("properties", {})
                        funding = props.get("total_funding", {}).get("value")
                        return {
                            "funding_total": float(funding) if funding else None,
                            "employee_count": props.get("employee_count", {}).get("value"),
                            "founded_year": props.get("founded_on", {}).get("value"),
                            "description": props.get("short_description"),
                            "confidence": 0.7,
                        }
            except Exception as e:
                logger.warning(f"Crunchbase enrichment failed for {company_name}: {e}")
        return None

    def _merge(self, base: EnrichmentResult, new_data: Dict[str, Any]) -> EnrichmentResult:
        """Merge new data into existing result, preferring non-None values."""
        merged = EnrichmentResult(
            domain=base.domain or new_data.get("domain"),
            company_name=base.company_name or new_data.get("company_name"),
            industry=base.industry or new_data.get("industry"),
            employee_count=base.employee_count or new_data.get("employee_count"),
            employee_range=base.employee_range or new_data.get("employee_range"),
            revenue_range=base.revenue_range or new_data.get("revenue_range"),
            funding_total=base.funding_total or new_data.get("funding_total"),
            tech_stack=list(set(base.tech_stack + (new_data.get("tech_stack") or []))),
            social_links={**base.social_links, **(new_data.get("social_links") or {})},
            contacts=base.contacts + (new_data.get("contacts") or []),
            description=base.description or new_data.get("description"),
            location=base.location or new_data.get("location"),
            founded_year=base.founded_year or new_data.get("founded_year"),
            confidence=max(base.confidence, new_data.get("confidence", 0)),
        )
        return merged


# Singleton
enrichment_service = EnrichmentService()