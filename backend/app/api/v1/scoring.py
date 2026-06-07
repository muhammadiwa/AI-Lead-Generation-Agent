"""Lead scoring API endpoints."""
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
    LeadScoreResponse,
    ScoringWeightsUpdate,
    success_response,
)
from app.core.errors import NotFoundError

router = APIRouter(tags=["Scoring"])

DEFAULT_WEIGHTS = {
    "icp_fit": 30,
    "tech_signal": 25,
    "budget_indicator": 20,
    "engagement_potential": 15,
    "urgency": 10,
}

DEFAULT_THRESHOLDS = {
    "hot": 70,
    "warm": 50,
    "cool": 30,
}


@router.get("/leads/{lead_id}/score", response_model=APIResponse)
async def get_lead_score(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get lead score breakdown."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    return success_response(
        data=LeadScoreResponse(
            lead_id=lead.id,
            total_score=float(lead.score_current or 0),
            breakdown=lead.score_breakdown or {},
            qualification=_get_qualification(float(lead.score_current or 0)),
        )
    )


@router.post("/scoring/recalculate", response_model=APIResponse)
async def recalculate_scores(
    lead_ids: Optional[list[uuid.UUID]] = None,
    db: AsyncSession = Depends(get_db),
):
    """Recalculate scores for all leads or specified leads."""
    query = select(Lead)
    if lead_ids:
        query = query.where(Lead.id.in_(lead_ids))

    result = await db.execute(query)
    leads = result.scalars().all()

    updated = 0
    for lead in leads:
        score = _calculate_lead_score(lead)
        lead.score_current = score["total"]
        lead.score_breakdown = score["breakdown"]
        lead.status = _determine_status(score["total"])
        db.add(lead)
        updated += 1

    return success_response(
        data={"recalculated": updated},
        meta={"total": len(leads)},
    )


@router.patch("/scoring/weights", response_model=APIResponse)
async def update_scoring_weights(
    weights: ScoringWeightsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update scoring dimension weights."""
    # Find or create active scoring config
    result = await db.execute(
        select(ScoringConfig).where(ScoringConfig.is_active == True)
    )
    config = result.scalar_one_or_none()

    if config:
        config.weights = weights.model_dump()
    else:
        config = ScoringConfig(
            name="Default Scoring Config",
            description="Auto-generated scoring configuration",
            weights=weights.model_dump(),
            thresholds=DEFAULT_THRESHOLDS,
            is_active=True,
        )
    db.add(config)

    return success_response(data={"weights": weights.model_dump()})


def _calculate_lead_score(lead: Lead) -> dict:
    """Calculate lead score based on available data dimensions."""
    breakdown = {}

    # ICP Fit Score (0-30)
    icp_score = 0
    if lead.industry:
        icp_score += 10
    if lead.employee_count and 10 <= lead.employee_count <= 500:
        icp_score += 5
    if lead.location_country:
        icp_score += 5
    if lead.founded_year:
        age = 2026 - lead.founded_year
        if 2 <= age <= 15:
            icp_score += 5
    if lead.tech_stack:
        icp_score += 5
    breakdown["icp_fit"] = min(icp_score, 30)

    # Tech Signal Score (0-25)
    tech_score = 5  # base for having a tech presence
    if lead.tech_stack:
        techs = lead.tech_stack.get("detected_technologies", [])
        if len(techs) > 0:
            tech_score += 5
        # More tech detected = more likely to need dev services
        if len(techs) > 3:
            tech_score += 5
    if lead.company_github_url:
        tech_score += 5
    if lead.description and ("react" in lead.description.lower() or "python" in lead.description.lower()):
        tech_score += 5
    breakdown["tech_signal"] = min(tech_score, 25)

    # Budget Indicator (0-20)
    budget_score = 5  # base
    if lead.funding_total and lead.funding_total > 0:
        budget_score += 8
    if lead.employee_count and lead.employee_count > 20:
        budget_score += 4
    if lead.funding_rounds and len(lead.funding_rounds) > 0:
        budget_score += 3
    breakdown["budget_indicator"] = min(budget_score, 20)

    # Engagement Potential (0-15)
    engagement_score = 3  # base
    if lead.description and len(lead.description) > 50:
        engagement_score += 4
    if lead.social_links:
        engagement_score += 4
    if lead.company_url:
        engagement_score += 4
    breakdown["engagement_potential"] = min(engagement_score, 15)

    # Urgency (0-10)
    urgency_score = 2  # base
    if lead.status in ("discovered", "scored"):
        urgency_score += 3
    if lead.notes and "urgent" in lead.notes.lower():
        urgency_score += 5
    breakdown["urgency"] = min(urgency_score, 10)

    total = sum(breakdown.values())

    return {
        "total": round(float(total), 2),
        "breakdown": breakdown,
        "weights": DEFAULT_WEIGHTS,
    }


def _determine_status(score: float) -> str:
    if score >= 70:
        return "qualified_hot"
    elif score >= 50:
        return "qualified_warm"
    elif score >= 30:
        return "qualified_cool"
    else:
        return "cold"


def _get_qualification(score: float) -> str:
    if score >= 70:
        return "hot"
    elif score >= 50:
        return "warm"
    elif score >= 30:
        return "cool"
    else:
        return "cold"