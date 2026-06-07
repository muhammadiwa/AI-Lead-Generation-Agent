"""Orchestrator that runs all collectors and merges results."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from app.collectors.base import BaseCollector, CollectedLead
from app.collectors.linkedin import LinkedInCollector
from app.collectors.github import GitHubCollector
from app.collectors.crunchbase import CrunchbaseCollector
from app.collectors.web_scraper import WebScraperCollector
from app.collectors.google_maps import GoogleMapsCollector
from app.collectors.social_media import SocialMediaCollector
from app.collectors.job_platforms import JobPlatformCollector
from app.collectors.business_directories import BusinessDirectoryCollector

logger = logging.getLogger(__name__)

# Registry of all available collectors
COLLECTOR_REGISTRY: Dict[str, Type[BaseCollector]] = {
    "linkedin": LinkedInCollector,
    "github": GitHubCollector,
    "crunchbase": CrunchbaseCollector,
    "web_scrape": WebScraperCollector,
    "google_maps": GoogleMapsCollector,
    "social_media": SocialMediaCollector,
    "job_platforms": JobPlatformCollector,
    "business_directory": BusinessDirectoryCollector,
}


class CollectionOrchestrator:
    """Orchestrates multi-source lead collection with deduplication."""

    def __init__(self):
        self._collectors: Dict[str, BaseCollector] = {}

    def get_collector(self, source: str, config: Optional[Dict] = None) -> Optional[BaseCollector]:
        """Get or create a collector by source name."""
        if source not in self._collectors:
            collector_cls = COLLECTOR_REGISTRY.get(source)
            if not collector_cls:
                logger.warning(f"Unknown collector source: {source}")
                return None
            self._collectors[source] = collector_cls(config)
        return self._collectors[source]

    async def collect_from_source(
        self, source: str, query: Dict[str, Any], max_results: int = 50
    ) -> List[CollectedLead]:
        """Collect leads from a single source."""
        collector = self.get_collector(source, query.get("config"))
        if not collector:
            return []
        return await collector.collect(query, max_results=max_results)

    async def collect_all(
        self, sources: List[str], query: Dict[str, Any], max_results: int = 50
    ) -> List[CollectedLead]:
        """Collect leads from multiple sources."""
        all_leads: List[CollectedLead] = []

        for source in sources:
            logger.info(f"Collecting from source: {source}")
            leads = await self.collect_from_source(source, query, max_results // len(sources))
            all_leads.extend(leads)

        # Deduplicate by company domain or name
        deduplicated = self._deduplicate(all_leads)
        return deduplicated[:max_results]

    def _deduplicate(self, leads: List[CollectedLead]) -> List[CollectedLead]:
        """Deduplicate leads by normalized domain or company name."""
        seen: set = set()
        unique: List[CollectedLead] = []

        for lead in leads:
            key = None
            if lead.company_domain:
                key = lead.company_domain.lower().strip()
            else:
                # Normalize company name for dedup
                name = lead.company_name.lower().strip()
                name = name.replace(" inc", "").replace(" llc", "").replace(" corp", "").replace(".", "").strip()
                key = name

            if key and key not in seen:
                seen.add(key)
                unique.append(lead)

        return unique


# Global orchestrator instance
orchestrator = CollectionOrchestrator()