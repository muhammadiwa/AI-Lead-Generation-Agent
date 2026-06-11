"""GitHub API explorer — finds companies by repo topics, tech stacks, and contributors."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.collectors.base import BaseCollector, CollectedContact, CollectedLead
from app.collectors.utils import async_random_delay, build_json_api_headers, rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


class GitHubCollector(BaseCollector):
    """Discover leads by exploring GitHub: repo stars, topics, contributors."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_name = "github"
        self.token = settings.github_token
        self._base_url = "https://api.github.com"
        rate_limiter.register_source("github", rate=5.0, burst=10)

    async def search(self, query: Dict[str, Any], max_results: int = 50) -> List[CollectedLead]:
        leads: List[CollectedLead] = []
        topics = query.get("topics", ["react", "python", "nodejs", "typescript", "aws", "kubernetes"])
        min_stars = query.get("min_stars", 100)
        look_for_outdated = query.get("look_for_outdated", True)

        headers = build_json_api_headers(api_key=self.token) if self.token else build_json_api_headers()

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            for topic in topics[:5]:  # Limit to first 5 topics
                await rate_limiter.wait("github")
                await async_random_delay(1.0, 2.0)

                try:
                    resp = await client.get(
                        f"{self._base_url}/search/repositories",
                        params={
                            "q": f"topic:{topic} stars:>={min_stars}",
                            "sort": "stars",
                            "order": "desc",
                            "per_page": min(25, max_results),
                        },
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        for repo in data.get("items", []):
                            if len(leads) >= max_results:
                                break

                            lead = await self._parse_repo_to_lead(repo, client, topic)
                            if lead:
                                leads.append(lead)
                except Exception as e:
                    logger.warning(f"GitHub search failed for topic '{topic}': {e}")

        return leads

    async def _parse_repo_to_lead(
        self, repo: Dict[str, Any], client: httpx.AsyncClient, topic: str
    ) -> Optional[CollectedLead]:
        """Convert a GitHub repo to a lead, enriching with owner info."""
        try:
            owner = repo.get("owner", {})
            owner_type = owner.get("type", "")
            # Skip individual users, focus on organizations
            if owner_type != "Organization":
                return None

            org_name = owner.get("login", "")
            org_url = owner.get("html_url", "")

            # Detect tech stack from repo topics and language
            repo_language = repo.get("language")
            repo_topics = repo.get("topics", [])
            tech_stack = {
                "primary_language": repo_language,
                "topics": repo_topics,
                "detected_from": f"github/repo:{repo.get('full_name', '')}",
            }

            lead = CollectedLead(
                company_name=org_name,
                company_domain=None,  # Would need org website
                company_url=org_url,
                company_github_url=org_url,
                description=repo.get("description"),
                tech_stack={"detected_technologies": [repo_language] if repo_language else [], "categories": tech_stack},
                source="github",
                source_id=repo.get("id"),
                source_url=repo.get("html_url"),
                confidence=0.6,
            )

            return lead
        except Exception as e:
            logger.warning(f"Failed to parse GitHub repo: {e}")
            return None