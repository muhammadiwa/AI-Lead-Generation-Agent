"""Lead management API endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.orchestrator import orchestrator
from app.database import get_db
from app.models import Lead, Contact
from app.schemas import (
    LeadCreate,
    LeadResponse,
    LeadUpdate,
    LeadListResponse,
    APIResponse,
    success_response,
    pagination_meta,
)
from app.collectors.base import CollectedLead
from app.core.errors import NotFoundError

router = APIRouter(tags=["Leads"])


@router.get("/leads", response_model=APIResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    source: Optional[str] = None,
    industry: Optional[str] = None,
    search: Optional[str] = None,
    min_score: Optional[float] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    """List/search leads with filtering, sorting, and pagination."""
    query = select(Lead)

    # Filters
    if status:
        query = query.where(Lead.status == status)
    if source:
        query = query.where(Lead.source == source)
    if industry:
        query = query.where(Lead.industry.ilike(f"%{industry}%"))
    if min_score is not None:
        query = query.where(Lead.score_current >= min_score)
    if search:
        like_pattern = f"%{search}%"
        query = query.where(
            Lead.company_name.ilike(like_pattern) | Lead.description.ilike(like_pattern)
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_col = getattr(Lead, sort_by, Lead.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    leads = result.scalars().all()

    return success_response(
        data=[LeadResponse.model_validate(l) for l in leads],
        meta=pagination_meta(page, limit, total),
    )


@router.get("/leads/{lead_id}", response_model=APIResponse)
async def get_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single lead with full profile."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    return success_response(data=LeadResponse.model_validate(lead))


@router.patch("/leads/{lead_id}", response_model=APIResponse)
async def update_lead(lead_id: uuid.UUID, update: LeadUpdate, db: AsyncSession = Depends(get_db)):
    """Update lead (status, score, notes, etc.)."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    db.add(lead)
    await db.flush()

    return success_response(data=LeadResponse.model_validate(lead))


@router.delete("/leads/{lead_id}", response_model=APIResponse)
async def delete_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Soft-delete a lead (blacklist)."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    lead.is_blacklisted = True
    lead.status = "archived"
    db.add(lead)

    return success_response(data={"id": lead_id, "status": "archived"})


@router.post("/leads", response_model=APIResponse, status_code=201)
async def create_lead(lead_data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Manually create a new lead."""
    lead = Lead(**lead_data.model_dump())
    db.add(lead)
    await db.flush()

    return success_response(data=LeadResponse.model_validate(lead), meta={"created": True})


@router.post("/leads/{lead_id}/enrich", response_model=APIResponse)
async def enrich_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Trigger enrichment for a single lead."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    # Trigger enrichment job (simplified for MVP)
    lead.status = "researching"
    db.add(lead)

    return success_response(data={"id": lead_id, "status": "enrichment_queued"})


@router.post("/leads/bulk/enrich", response_model=APIResponse)
async def bulk_enrich_leads(
    lead_ids: list[uuid.UUID],
    db: AsyncSession = Depends(get_db),
):
    """Batch enrich multiple leads."""
    result = await db.execute(select(Lead).where(Lead.id.in_(lead_ids)))
    leads = result.scalars().all()

    for lead in leads:
        lead.status = "researching"
    db.add_all(leads)

    return success_response(data={"enriched": len(leads), "status": "enrichment_queued"})