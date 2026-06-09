"""LLM integration — uses OpenAI/Claude for intelligent lead analysis."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LeadAnalysis:
    """Structured analysis result from LLM."""
    summary: str = ""
    pain_points: List[str] = field(default_factory=list)
    tech_needs: List[str] = field(default_factory=list)
    budget_estimate: Optional[str] = None
    decision_makers: List[str] = field(default_factory=list)
    recommended_approach: str = ""
    engagement_score: float = 0.0  # 0-100
    confidence: float = 0.0


# ─── Prompt template for lead analysis ───

LEAD_ANALYSIS_PROMPT = """You are a B2B lead qualification analyst. Analyze the following lead data and return a JSON response.

Lead Data:
- Company: {company_name}
- Domain: {company_domain}
- Industry: {industry}
- Description: {description}
- Employee Count: {employee_count}
- Location: {location_city}, {location_state}, {location_country}
- Tech Stack: {tech_stack}
- Funding: {funding_total} ({funding_currency})
- Tags: {tags}
- Notes: {notes}

Analyze this lead and return a JSON object with exactly these fields:
{{
    "summary": "Brief 1-2 sentence company summary",
    "pain_points": ["List of likely pain points this company faces related to software/tech"],
    "tech_needs": ["List of software development services they likely need"],
    "budget_estimate": "Estimated budget range (e.g., '10k-50k', '50k-200k', '200k+', or 'unknown')",
    "decision_makers": ["Likely decision maker titles for this company"],
    "recommended_approach": "Best outreach approach in 1 sentence",
    "engagement_score": <number between 0-100 indicating how likely they are to engage>,
    "confidence": <number between 0.0-1.0 indicating confidence in this analysis>
}}

Return ONLY valid JSON, no other text."""


class LLMAnalyzer:
    """Analyze lead data using LLM (OpenAI/Claude) with structured fallback."""

    def __init__(self):
        self.openai_key = settings.openai_api_key
        self.anthropic_key = settings.anthropic_api_key
        self._provider = self._detect_provider()

    def _detect_provider(self) -> Optional[str]:
        """Detect which LLM provider is configured."""
        if self.anthropic_key:
            return "anthropic"
        elif self.openai_key:
            return "openai"
        return None

    async def analyze(self, lead_data: Dict[str, Any]) -> LeadAnalysis:
        """Analyze a lead using LLM, with graceful fallback to heuristic analysis."""
        if self._provider:
            try:
                if self._provider == "anthropic":
                    return await self._analyze_anthropic(lead_data)
                else:
                    return await self._analyze_openai(lead_data)
            except Exception as e:
                logger.warning(f"LLM analysis failed (using fallback): {e}")

        return self._fallback_analysis(lead_data)

    async def _analyze_anthropic(self, lead_data: Dict[str, Any]) -> LeadAnalysis:
        """Analyze using Anthropic Claude API."""
        try:
            import httpx

            prompt = LEAD_ANALYSIS_PROMPT.format(
                company_name=lead_data.get("company_name", "Unknown"),
                company_domain=lead_data.get("company_domain", ""),
                industry=lead_data.get("industry", ""),
                description=(lead_data.get("description") or "")[:500],
                employee_count=lead_data.get("employee_count", "unknown"),
                location_city=lead_data.get("location_city", ""),
                location_state=lead_data.get("location_state", ""),
                location_country=lead_data.get("location_country", ""),
                tech_stack=json.dumps(lead_data.get("tech_stack", {})),
                funding_total=lead_data.get("funding_total", "unknown"),
                funding_currency=lead_data.get("funding_currency", "USD"),
                tags=", ".join(lead_data.get("tags") or []),
                notes=(lead_data.get("notes") or "")[:300],
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 1000,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )

                if resp.status_code == 200:
                    content = resp.json()["content"][0]["text"]
                    return self._parse_llm_response(content)

                logger.warning(f"Anthropic API error: {resp.status_code}")
        except ImportError:
            logger.warning("httpx not installed, cannot call LLM API")
        except Exception as e:
            logger.warning(f"Anthropic analysis failed: {e}")

        return self._fallback_analysis(lead_data)

    async def _analyze_openai(self, lead_data: Dict[str, Any]) -> LeadAnalysis:
        """Analyze using OpenAI API."""
        try:
            import httpx

            prompt = LEAD_ANALYSIS_PROMPT.format(
                company_name=lead_data.get("company_name", "Unknown"),
                company_domain=lead_data.get("company_domain", ""),
                industry=lead_data.get("industry", ""),
                description=(lead_data.get("description") or "")[:500],
                employee_count=lead_data.get("employee_count", "unknown"),
                location_city=lead_data.get("location_city", ""),
                location_state=lead_data.get("location_state", ""),
                location_country=lead_data.get("location_country", ""),
                tech_stack=json.dumps(lead_data.get("tech_stack", {})),
                funding_total=lead_data.get("funding_total", "unknown"),
                funding_currency=lead_data.get("funding_currency", "USD"),
                tags=", ".join(lead_data.get("tags") or []),
                notes=(lead_data.get("notes") or "")[:300],
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o",
                        "max_tokens": 1000,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )

                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    return self._parse_llm_response(content)

                logger.warning(f"OpenAI API error: {resp.status_code}")
        except ImportError:
            logger.warning("httpx not installed, cannot call LLM API")
        except Exception as e:
            logger.warning(f"OpenAI analysis failed: {e}")

        return self._fallback_analysis(lead_data)

    def _parse_llm_response(self, content: str) -> LeadAnalysis:
        """Parse LLM JSON response into LeadAnalysis."""
        try:
            # Try to extract JSON from the response
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)
            return LeadAnalysis(
                summary=data.get("summary", ""),
                pain_points=data.get("pain_points", []),
                tech_needs=data.get("tech_needs", []),
                budget_estimate=data.get("budget_estimate"),
                decision_makers=data.get("decision_makers", []),
                recommended_approach=data.get("recommended_approach", ""),
                engagement_score=float(data.get("engagement_score", 0)),
                confidence=float(data.get("confidence", 0)),
            )
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return self._fallback_analysis({})

    def _fallback_analysis(self, lead_data: Dict[str, Any]) -> LeadAnalysis:
        """Heuristic fallback when LLM is unavailable."""
        pain_points = []
        tech_needs = []
        score = 50.0

        desc = (lead_data.get("description") or "").lower()
        industry = (lead_data.get("industry") or "").lower()
        tech_stack = lead_data.get("tech_stack") or {}

        # Detect pain points from description
        if any(word in desc for word in ["scale", "grow", "expand"]):
            pain_points.append("Scaling challenges")
            score += 10
        if any(word in desc for word in ["migrate", "legacy", "modernize"]):
            pain_points.append("Technical debt / legacy systems")
            score += 10
        if any(word in desc for word in ["manual", "inefficient", "slow"]):
            pain_points.append("Inefficient manual processes")
            score += 10
        if any(word in desc for word in ["compete", "competition", "market"]):
            pain_points.append("Competitive pressure")
            score += 8

        # Detect tech needs
        if "saas" in industry or "software" in industry:
            tech_needs.append("Product development & scaling")
            score += 5
        if "fintech" in industry or "finance" in industry:
            tech_needs.append("Secure, compliant software systems")
            score += 5
        if "health" in industry or "medical" in industry:
            tech_needs.append("HIPAA-compliant development")
            score += 5
        if "ecommerce" in industry or "retail" in industry:
            tech_needs.append("E-commerce platform development")
            score += 5

        # Detected tech stack
        detected = tech_stack.get("detected_technologies", [])
        if detected:
            tech_needs.append(f"Expertise in {', '.join(detected[:3])}")
            score += 5

        # Employee count signals
        emp_count = lead_data.get("employee_count")
        if emp_count:
            if 10 <= emp_count <= 50:
                pain_points.append("Small team, likely needs external development help")
                score += 15
            elif 51 <= emp_count <= 200:
                pain_points.append("Growing company, may need to supplement in-house team")
                score += 10
            elif emp_count > 200:
                pain_points.append("Large organization, may need specialized expertise")
                score += 5

        # Funding signals
        funding = lead_data.get("funding_total")
        if funding and funding > 0:
            score += 10
            pain_points.append("Recently funded — likely has budget for development")

        summary = f"{lead_data.get('company_name', 'Unknown')} — "
        if industry:
            summary += f"{industry} company"
        else:
            summary += "Technology company"
        if emp_count:
            summary += f" with ~{emp_count} employees"

        return LeadAnalysis(
            summary=summary,
            pain_points=pain_points[:5],
            tech_needs=tech_needs[:5],
            budget_estimate=self._estimate_budget(funding, emp_count),
            decision_makers=["CTO", "VP Engineering", "Head of Product"],
            recommended_approach=f"Highlight relevant expertise in {', '.join(tech_needs[:2]) if tech_needs else 'software development'}",
            engagement_score=min(score, 95),
            confidence=0.6,
        )

    def _estimate_budget(self, funding: Optional[float], emp_count: Optional[int]) -> str:
        """Estimate budget range based on available data."""
        if funding and funding > 5_000_000:
            return "200k+"
        elif funding and funding > 1_000_000:
            return "50k-200k"
        elif emp_count and emp_count > 50:
            return "50k-200k"
        elif emp_count and emp_count > 10:
            return "10k-50k"
        return "unknown"


# Singleton
llm_analyzer = LLMAnalyzer()