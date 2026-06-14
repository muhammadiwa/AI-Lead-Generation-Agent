"""Pipeline/stage management — move leads through qualification stages."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead, Message
from app.schemas import APIResponse, LeadResponse
from app.core import success_response
from app.core.errors import NotFoundError

router = APIRouter(tags=["Pipeline"])

# Lead lifecycle statuses in order
PIPELINE_STAGES = [
    "discovered",
    "researching",
    "researched",
    "scored",
    "qualified_hot",
    "qualified_warm",
    "qualified_cool",
    "cold",
    "contacted",
    "responded",
    "meeting_scheduled",
    "converted",
    "lost",
    "archived",
]


@router.get("/pipeline", response_model=APIResponse)
async def get_pipeline(db: AsyncSession = Depends(get_db)):
    """Get the full pipeline with lead counts per stage."""
    result = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )
    counts = {row[0]: row[1] for row in result.all()}

    pipeline = []
    for stage in PIPELINE_STAGES:
        pipeline.append({
            "stage": stage,
            "count": counts.get(stage, 0),
            "display_name": stage.replace("_", " ").title(),
        })

    total = sum(p["count"] for p in pipeline)
    return success_response(data={"pipeline": pipeline, "total_leads": total})


@router.get("/pipeline/{stage}/leads", response_model=APIResponse)
async def get_pipeline_stage(
    stage: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get all leads in a specific pipeline stage."""
    if stage not in PIPELINE_STAGES:
        return success_response(data={"leads": [], "total": 0, "stage": stage})

    query = select(Lead).where(Lead.status == stage).order_by(Lead.updated_at.desc())
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    leads = result.scalars().all()

    return success_response(
        data={
            "stage": stage,
            "leads": [LeadResponse.model_validate(l) for l in leads],
            "total": total,
            "page": page,
            "limit": limit,
        }
    )


@router.post("/pipeline/{lead_id}/move", response_model=APIResponse)
async def move_lead_stage(
    lead_id: uuid.UUID,
    target_stage: str,
    db: AsyncSession = Depends(get_db),
):
    """Move a lead to a different pipeline stage."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    if target_stage not in PIPELINE_STAGES:
        return success_response(data={
            "error": f"Invalid stage: {target_stage}. Valid stages: {PIPELINE_STAGES}"
        })

    lead.status = target_stage
    db.add(lead)

    return success_response(data={
        "lead_id": str(lead.id),
        "company_name": lead.company_name,
        "previous_stage": lead.status,
        "current_stage": target_stage,
    })


@router.post("/pipeline/bulk-move", response_model=APIResponse)
async def bulk_move_leads(
    lead_ids: list[uuid.UUID],
    target_stage: str,
    db: AsyncSession = Depends(get_db),
):
    """Move multiple leads to a stage."""
    if target_stage not in PIPELINE_STAGES:
        return success_response(data={"error": f"Invalid stage: {target_stage}"})

    result = await db.execute(select(Lead).where(Lead.id.in_(lead_ids)))
    leads = result.scalars().all()
    moved = 0

    for lead in leads:
        lead.status = target_stage
        db.add(lead)
        moved += 1

    return success_response(data={
        "moved": moved,
        "target_stage": target_stage,
    })


@router.get("/pipeline/metrics", response_model=APIResponse)
async def get_pipeline_metrics(db: AsyncSession = Depends(get_db)):
    """Get pipeline conversion metrics."""
    result = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )
    counts = dict(result.all())

    metrics = {
        "total_leads": sum(counts.values()),
        "stage_counts": {s: counts.get(s, 0) for s in PIPELINE_STAGES},
        "converted": counts.get("converted", 0),
        "lost": counts.get("lost", 0),
        "active": sum(counts.get(s, 0) for s in ["qualified_hot", "qualified_warm", "contacted", "responded"]),
        "needs_review": sum(counts.get(s, 0) for s in ["discovered", "researching", "scored"]),
    }

    if metrics["total_leads"] > 0:
        metrics["conversion_rate"] = round(
            metrics["converted"] / metrics["total_leads"] * 100, 2
        )
    else:
        metrics["conversion_rate"] = 0.0

    return success_response(data=metrics)