"""Enhanced scoring engine — combines heuristic, signal, LLM, and enrichment data."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.models import Lead
from app.qualification.signal_detector import LeadSignal, signal_detector
from app.qualification.llm_analyzer import LeadAnalysis, llm_analyzer
from app.qualification.enrichment import EnrichmentResult, enrichment_service

logger = logging.getLogger(__name__)


@dataclass
class QualificationResult:
    """Complete qualification result for a lead."""
    lead_id: str
    total_score: float            # 0-100
    qualification: str            # 'hot', 'warm', 'cool', 'cold'
    signals: List[Dict[str, Any]] = field(default_factory=list)
    llm_analysis: Dict[str, Any] = field(default_factory=dict)
    enrichment: Dict[str, Any] = field(default_factory=dict)
    breakdown: Dict[str, float] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


# Scoring weights for different dimensions
DIMENSION_WEIGHTS = {
    "icp_fit": 0.25,              # Industry, company size, location match
    "tech_signal": 0.20,          # Tech stack signals
    "intent_signals": 0.20,       # NLP-detected intent (hiring, pain points)
    "enrichment": 0.10,           # External data quality
    "funding_budget": 0.15,       # Budget indicators
    "engagement": 0.10,           # Engagement potential
}

THRESHOLDS = {
    "hot": 70,
    "warm": 50,
    "cool": 30,
}


class QualificationScorer:
    """Multi-dimensional lead scorer combining heuristic, signal, and AI analysis."""

    async def qualify(self, lead: Lead) -> QualificationResult:
        """Run the full qualification pipeline on a lead."""
        lead_data = self._lead_to_dict(lead)

        # Step 1: Detect signals from content
        signals = signal_detector.analyze(lead_data)

        # Step 2: LLM analysis
        analysis = await llm_analyzer.analyze(lead_data)

        # Step 3: Enrichment
        enrichment = EnrichmentResult()
        if lead.company_domain:
            enrichment = await enrichment_service.enrich(
                lead.company_domain, lead.company_name
            )

        # Step 4: Calculate scores
        breakdown = {}
        breakdown["icp_fit"] = self._score_icp_fit(lead, enrichment)
        breakdown["tech_signal"] = self._score_tech_signal(lead, signals)
        breakdown["intent_signals"] = self._score_intent_signals(signals)
        breakdown["enrichment"] = self._score_enrichment_quality(enrichment)
        breakdown["funding_budget"] = self._score_budget(lead, signals, analysis)
        breakdown["engagement"] = self._score_engagement(lead, signals, analysis)

        # Step 5: Weighted total
        total_score = sum(
            breakdown.get(dim, 0) * DIMENSION_WEIGHTS.get(dim, 0)
            for dim in DIMENSION_WEIGHTS
        )
        total_score = round(min(total_score, 100), 2)

        qualification = self._determine_qualification(total_score)

        return QualificationResult(
            lead_id=str(lead.id),
            total_score=total_score,
            qualification=qualification,
            signals=[self._signal_to_dict(s) for s in signals],
            llm_analysis={
                "summary": analysis.summary,
                "pain_points": analysis.pain_points,
                "tech_needs": analysis.tech_needs,
                "budget_estimate": analysis.budget_estimate,
                "decision_makers": analysis.decision_makers,
                "recommended_approach": analysis.recommended_approach,
                "engagement_score": analysis.engagement_score,
                "confidence": analysis.confidence,
            },
            enrichment={
                "employees": enrichment.employee_count,
                "revenue": enrichment.revenue_range,
                "funding": enrichment.funding_total,
                "contacts_found": len(enrichment.contacts),
                "tech_found": enrichment.tech_stack,
                "confidence": enrichment.confidence,
            },
            breakdown={
                dim: round(breakdown.get(dim, 0), 2)
                for dim in DIMENSION_WEIGHTS
            },
        )

    def _lead_to_dict(self, lead: Lead) -> Dict[str, Any]:
        """Convert a SQLAlchemy Lead model to a dict for analysis."""
        return {
            "id": str(lead.id),
            "company_name": lead.company_name,
            "company_domain": lead.company_domain,
            "company_url": lead.company_url,
            "description": lead.description,
            "industry": lead.industry,
            "employee_count": lead.employee_count,
            "location_city": lead.location_city,
            "location_state": lead.location_state,
            "location_country": lead.location_country,
            "founded_year": lead.founded_year,
            "funding_total": float(lead.funding_total) if lead.funding_total else None,
            "funding_currency": lead.funding_currency,
            "funding_rounds": lead.funding_rounds,
            "tech_stack": lead.tech_stack,
            "social_links": lead.social_links,
            "tags": lead.tags,
            "notes": lead.notes,
            "source": lead.source,
        }

    def _score_icp_fit(self, lead: Lead, enrichment: EnrichmentResult) -> float:
        """Score ICP fit (0-100)."""
        score = 0.0
        max_score = 100.0

        # Industry match (40 pts max)
        if lead.industry:
            industry = lead.industry.lower()
            target_industries = ["software", "saas", "fintech", "healthtech", "ecommerce",
                                 "technology", "ai", "analytics", "data", "devtools"]
            if any(ti in industry for ti in target_industries):
                score += 40

        # Company size (20 pts max)
        if lead.employee_count:
            if 10 <= lead.employee_count <= 500:
                score += 20
            elif lead.employee_count > 500:
                score += 10

        # Location (20 pts max)
        if lead.location_country:
            us_states = ["us", "united states", "ca", "usa", "new york", "california",
                         "texas", "washington", "massachusetts", "illinois"]
            if lead.location_country.lower() in us_states:
                score += 20
            elif lead.location_country.lower() in ["gb", "uk", "united kingdom", "de", "germany",
                                                    "ca", "canada", "au", "australia"]:
                score += 15

        # Enrichment data (20 pts max)
        if enrichment.industry:
            score += 10
        if enrichment.employee_count:
            score += 5
        if enrichment.revenue_range:
            score += 5

        return min(score, max_score)

    def _score_tech_signal(self, lead: Lead, signals: List[LeadSignal]) -> float:
        """Score tech signals (0-100)."""
        score = 20.0  # Base: has a tech presence

        if lead.tech_stack:
            techs = lead.tech_stack.get("detected_technologies", []) if isinstance(lead.tech_stack, dict) else []
            score += min(len(techs) * 5, 20)

        if lead.company_github_url:
            score += 15
        if lead.company_linkedin_url:
            score += 10

        # Boost from signals
        for s in signals:
            if s.signal_type == "tech_debt":
                score += 15
            elif s.signal_type == "modern_tech":
                score += 5
            elif s.signal_type == "pain_point":
                score += 10

        return min(score, 100)

    def _score_intent_signals(self, signals: List[LeadSignal]) -> float:
        """Score intent signals (0-100)."""
        score = 0.0
        for s in signals:
            if s.signal_type in ("seeking_cto", "seeking_services"):
                score += 30
            elif s.signal_type == "hiring_developers":
                score += 20
            elif s.signal_type == "pain_point":
                score += 15
            elif s.signal_type == "time_sensitive":
                score += 15
            elif s.signal_type == "mass_hiring":
                score += 10
            elif s.signal_type == "competitive_pressure":
                score += 10

        return min(score, 100)

    def _score_enrichment_quality(self, enrichment: EnrichmentResult) -> float:
        """Score how much enrichment data was available (0-100)."""
        score = 0.0
        if enrichment.industry:
            score += 15
        if enrichment.employee_count:
            score += 15
        if enrichment.revenue_range:
            score += 15
        if enrichment.tech_stack:
            score += 15
        if enrichment.contacts:
            score += min(len(enrichment.contacts) * 5, 20)
        if enrichment.funding_total:
            score += 10
        if enrichment.description:
            score += 10

        return min(score, 100)

    def _score_budget(self, lead: Lead, signals: List[LeadSignal],
                      analysis: LeadAnalysis) -> float:
        """Score budget indicators (0-100)."""
        score = 0.0

        # Direct funding data
        if lead.funding_total:
            if lead.funding_total > 10_000_000:
                score += 40
            elif lead.funding_total > 1_000_000:
                score += 30
            elif lead.funding_total > 100_000:
                score += 20
            else:
                score += 10

        # Company size as budget proxy
        if lead.employee_count:
            if lead.employee_count > 200:
                score += 20
            elif lead.employee_count > 50:
                score += 15
            elif lead.employee_count > 10:
                score += 10

        # LLM budget estimate
        if analysis.budget_estimate and analysis.budget_estimate != "unknown":
            if "200k" in analysis.budget_estimate:
                score += 25
            elif "50k" in analysis.budget_estimate:
                score += 15
            elif "10k" in analysis.budget_estimate:
                score += 5

        # Funding signals
        for s in signals:
            if s.signal_type == "recent_funding":
                score += 15
            elif s.signal_type == "rapid_growth":
                score += 10

        return min(score, 100)

    def _score_engagement(self, lead: Lead, signals: List[LeadSignal],
                          analysis: LeadAnalysis) -> float:
        """Score engagement potential (0-100)."""
        score = 10.0  # Base

        # Data completeness ~ engagement readiness
        if lead.description:
            score += 10
        if lead.social_links:
            score += 10
        if lead.company_url:
            score += 10
        if lead.contacts:
            score += 10

        # Engagement signals
        for s in signals:
            if s.signal_type == "active_development":
                score += 15
            elif s.signal_type == "pain_point":
                score += 15

        # LLM engagement score
        if analysis.engagement_score > 0:
            score += analysis.engagement_score * 0.2

        return min(score, 100)

    def _determine_qualification(self, score: float) -> str:
        """Map score to qualification tier."""
        if score >= 70:
            return "hot"
        elif score >= 50:
            return "warm"
        elif score >= 30:
            return "cool"
        else:
            return "cold"

    @staticmethod
    def _signal_to_dict(signal: LeadSignal) -> Dict[str, Any]:
        return {
            "type": signal.signal_type,
            "strength": signal.strength,
            "source": signal.source,
            "evidence": signal.evidence,
        }


# Singleton
qualification_scorer = QualificationScorer()