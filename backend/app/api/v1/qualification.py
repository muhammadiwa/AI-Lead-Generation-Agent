"""Lead qualification API endpoints — enhanced scoring with NLP, LLM, enrichment, embeddings."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead, ScoringConfig
from app.schemas import (
    APIResponse,
    success_response,
)
from app.core.errors import NotFoundError
from app.qualification.scorer import qualification_scorer
from app.qualification.embedder import embedding_service
from app.qualification.signal_detector import signal_detector
from app.qualification.llm_analyzer import llm_analyzer
from app.qualification.enrichment import enrichment_service

router = APIRouter(tags=["Qualification"])


@router.post("/scoring/qualify", response_model=APIResponse)
async def qualify_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Run the full qualification pipeline on a single lead:
    1. Signal detection (NLP patterns)
    2. LLM analysis (OpenAI/Claude)
    3. Company enrichment (Clearbit, Hunter, Crunchbase)
    4. Multi-dimensional scoring
    5. Embedding generation for similarity search
    """
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    qualification = await qualification_scorer.qualify(lead)

    lead_data = qualification_scorer._lead_to_dict(lead)
    embedding = await embedding_service.embed(lead_data)

    lead.score_current = qualification.total_score
    lead.score_breakdown = {
        "total": qualification.total_score,
        "qualification": qualification.qualification,
        "dimensions": qualification.breakdown,
        "signals": qualification.signals,
        "llm_analysis": qualification.llm_analysis,
        "enrichment": qualification.enrichment,
    }
    lead.status = _determine_status(qualification.total_score)
    db.add(lead)

    return success_response(data={
        "lead_id": qualification.lead_id,
        "total_score": qualification.total_score,
        "qualification": qualification.qualification,
        "breakdown": qualification.breakdown,
        "signals": qualification.signals,
        "llm_analysis": qualification.llm_analysis,
        "enrichment": qualification.enrichment,
        "embedding_generated": embedding is not None,
    })


@router.post("/scoring/qualify-batch", response_model=APIResponse)
async def qualify_lead_batch(
    lead_ids: list[uuid.UUID],
    db: AsyncSession = Depends(get_db),
):
    """Run qualification pipeline for multiple leads."""
    result = await db.execute(select(Lead).where(Lead.id.in_(lead_ids)))
    leads = result.scalars().all()

    results = []
    for lead in leads:
        qualification = await qualification_scorer.qualify(lead)
        lead.score_current = qualification.total_score
        lead.score_breakdown = {
            "total": qualification.total_score,
            "qualification": qualification.qualification,
            "dimensions": qualification.breakdown,
            "signals": qualification.signals,
            "llm_analysis": qualification.llm_analysis,
        }
        lead.status = _determine_status(qualification.total_score)
        db.add(lead)
        results.append({
            "lead_id": qualification.lead_id,
            "score": qualification.total_score,
            "qualification": qualification.qualification,
        })

    return success_response(data={
        "qualified": len(results),
        "results": results,
    })


@router.get("/leads/{lead_id}/signals", response_model=APIResponse)
async def get_lead_signals(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Detect and return NLP signals from a lead's content without full scoring."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    lead_data = qualification_scorer._lead_to_dict(lead)
    signals = signal_detector.analyze(lead_data)

    return success_response(data={
        "lead_id": str(lead.id),
        "signals": [{
            "type": s.signal_type,
            "strength": s.strength,
            "source": s.source,
            "evidence": s.evidence,
            "category": s.category,
        } for s in signals],
        "total_signals": len(signals),
    })


@router.post("/leads/{lead_id}/analyze", response_model=APIResponse)
async def analyze_lead_llm(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Run LLM analysis on a lead."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    lead_data = qualification_scorer._lead_to_dict(lead)
    analysis = await llm_analyzer.analyze(lead_data)

    return success_response(data={
        "lead_id": str(lead.id),
        "summary": analysis.summary,
        "pain_points": analysis.pain_points,
        "tech_needs": analysis.tech_needs,
        "budget_estimate": analysis.budget_estimate,
        "decision_makers": analysis.decision_makers,
        "recommended_approach": analysis.recommended_approach,
        "engagement_score": analysis.engagement_score,
        "confidence": analysis.confidence,
    })


@router.post("/leads/{lead_id}/enrich", response_model=APIResponse)
async def enrich_lead_endpoint(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Enrich a lead with data from external APIs (Clearbit, Hunter, Crunchbase)."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    if not lead.company_domain:
        return success_response(data={
            "lead_id": str(lead.id),
            "enriched": False,
            "message": "No company domain available for enrichment",
        })

    enrichment = await enrichment_service.enrich(lead.company_domain, lead.company_name)

    if enrichment.company_name:
        lead.company_name = enrichment.company_name
    if enrichment.industry:
        lead.industry = enrichment.industry
    if enrichment.employee_count:
        lead.employee_count = enrichment.employee_count
    if enrichment.funding_total:
        lead.funding_total = enrichment.funding_total
    if enrichment.description:
        lead.description = enrichment.description
    if enrichment.social_links:
        existing = lead.social_links or {}
        existing.update(enrichment.social_links)
        lead.social_links = existing
    if enrichment.founded_year:
        lead.founded_year = enrichment.founded_year
    db.add(lead)

    return success_response(data={
        "lead_id": str(lead.id),
        "enriched": True,
        "data": {
            "employees": enrichment.employee_count,
            "revenue": enrichment.revenue_range,
            "funding": enrichment.funding_total,
            "industry": enrichment.industry,
            "description": enrichment.description,
            "contacts_found": len(enrichment.contacts),
            "tech_stack": enrichment.tech_stack,
            "confidence": enrichment.confidence,
        },
    })


@router.post("/scoring/similar", response_model=APIResponse)
async def find_similar_leads(
    lead_id: uuid.UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Find leads similar to a given lead using vector embeddings."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    source_lead = result.scalar_one_or_none()
    if not source_lead:
        raise NotFoundError("Lead", str(lead_id))

    source_data = qualification_scorer._lead_to_dict(source_lead)
    source_embedding = await embedding_service.embed(source_data)
    if not source_embedding:
        return success_response(data={
            "lead_id": str(lead_id),
            "similar_leads": [],
            "message": "Could not generate embedding for source lead",
        })

    all_leads = await db.execute(
        select(Lead).where(Lead.id != lead_id).limit(100)
    )
    similar = []
    for other_lead in all_leads.scalars().all():
        other_data = qualification_scorer._lead_to_dict(other_lead)
        other_embedding = await embedding_service.embed(other_data)
        if other_embedding:
            similarity = embedding_service.cosine_similarity(
                source_embedding.vector,
                other_embedding.vector,
            )
            similar.append({
                "lead_id": str(other_lead.id),
                "company_name": other_lead.company_name,
                "score": float(other_lead.score_current or 0),
                "similarity": round(float(similarity), 4),
            })

    similar.sort(key=lambda x: x["similarity"], reverse=True)

    return success_response(data={
        "source_lead_id": str(lead_id),
        "similar_leads": similar[:limit],
    })


def _determine_status(score: float) -> str:
    if score >= 70:
        return "qualified_hot"
    elif score >= 50:
        return "qualified_warm"
    elif score >= 30:
        return "qualified_cool"
    else:
        return "cold"