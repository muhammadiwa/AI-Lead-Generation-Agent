"""Abstract base class for data collectors."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CollectedLead:
    """Standardized lead data from any source."""
    company_name: str
    company_domain: Optional[str] = None
    company_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_github_url: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    founded_year: Optional[int] = None
    funding_total: Optional[float] = None
    funding_currency: Optional[str] = "USD"
    funding_rounds: Optional[List[Dict[str, Any]]] = None
    tech_stack: Optional[Dict[str, Any]] = None
    social_links: Optional[Dict[str, Any]] = None
    source: str = ""
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    contacts: List["CollectedContact"] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None
    confidence: float = 0.5


@dataclass
class CollectedContact:
    """Standardized contact data."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: Optional[str] = None
    role_title: Optional[str] = None
    is_decision_maker: bool = False
    is_primary: bool = False


class BaseCollector(ABC):
    """Abstract base class for all data source collectors."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.source_name: str = "base"

    @abstractmethod
    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        """Execute a search against the source and return collected leads."""
        ...

    async def validate(self, lead: CollectedLead) -> bool:
        """Validate a collected lead before insertion. Override for source-specific validation."""
        return bool(lead.company_name)

    async def enrich(self, lead: CollectedLead) -> CollectedLead:
        """Post-collection enrichment hook. Override to add source-specific data."""
        return lead

    async def collect(
        self, query: Dict[str, Any], max_results: int = 50
    ) -> List[CollectedLead]:
        """Full collection pipeline: search → validate → enrich."""
        results = await self.search(query, max_results=max_results)
        validated: List[CollectedLead] = []
        for lead in results:
            lead.source = self.source_name
            if await self.validate(lead):
                enriched = await self.enrich(lead)
                validated.append(enriched)
        return validated