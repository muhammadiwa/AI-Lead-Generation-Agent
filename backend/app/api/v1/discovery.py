"""Lead discovery API endpoints."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import CollectedLead
from app.collectors.orchestrator import orchestrator
from app.database import get_db
from app.models import Lead, DiscoveryCampaign, LeadSource, ICPProfile
from app.schemas import (
    APIResponse,
    DiscoveryCampaignCreate,
    DiscoveryCampaignResponse,
    DiscoverySearchRequest,
    LeadCreate,
    LeadResponse,
    success_response,
)
from app.core.errors import NotFoundError, AppError

router = APIRouter(tags=["Discovery"])


@router.post("/discovery/search", response_model=APIResponse)
async def discovery_search(
    request: DiscoverySearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """One-time search across selected sources. Triggers collection and stores results."""
    sources = request.sources
    config: Dict[str, Any] = request.config

    # Get ICP filters if profile specified
    if request.icp_profile_id:
        icp_result = await db.execute(
            select(ICPProfile).where(ICPProfile.id == request.icp_profile_id)
        )
        icp_profile = icp_result.scalar_one_or_none()
        if icp_profile:
            config["icp_profile_id"] = str(request.icp_profile_id)

    # Collect leads from all requested sources
    collected_leads = await orchestrator.collect_all(
        sources=sources,
        query=config,
        max_results=request.max_leads,
    )

    # Store collected leads in database
    stored_ids: List[str] = []
    for collected in collected_leads:
        lead_id = await _store_lead(db, collected)
        if lead_id:
            stored_ids.append(str(lead_id))

    await db.commit()

    return success_response(
        data={
            "total_collected": len(collected_leads),
            "total_stored": len(stored_ids),
            "lead_ids": stored_ids,
        },
        meta={
            "sources": sources,
            "max_leads": request.max_leads,
        },
    )


@router.post("/discovery/campaigns", response_model=APIResponse, status_code=201)
async def create_discovery_campaign(
    campaign: DiscoveryCampaignCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a recurring discovery campaign."""
    db_campaign = DiscoveryCampaign(
        name=campaign.name,
        icp_profile_id=campaign.icp_profile_id,
        sources=campaign.sources,
        schedule_cron=campaign.schedule_cron,
        max_leads_per_run=campaign.max_leads_per_run,
        config=campaign.config,
    )
    db.add(db_campaign)
    await db.flush()

    return success_response(
        data=DiscoveryCampaignResponse.model_validate(db_campaign),
        meta={"created": True},
    )


@router.get("/discovery/campaigns", response_model=APIResponse)
async def list_discovery_campaigns(db: AsyncSession = Depends(get_db)):
    """List all discovery campaigns."""
    result = await db.execute(select(DiscoveryCampaign).order_by(DiscoveryCampaign.created_at.desc()))
    campaigns = result.scalars().all()

    return success_response(
        data=[DiscoveryCampaignResponse.model_validate(c) for c in campaigns]
    )


@router.patch("/discovery/campaigns/{campaign_id}", response_model=APIResponse)
async def update_discovery_campaign(
    campaign_id: uuid.UUID,
    update: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update a discovery campaign's configuration."""
    result = await db.execute(select(DiscoveryCampaign).where(DiscoveryCampaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise NotFoundError("DiscoveryCampaign", str(campaign_id))

    for field, value in update.items():
        if hasattr(campaign, field):
            setattr(campaign, field, value)

    db.add(campaign)
    return success_response(data=DiscoveryCampaignResponse.model_validate(campaign))


@router.delete("/discovery/campaigns/{campaign_id}", response_model=APIResponse)
async def delete_discovery_campaign(campaign_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Stop and delete a discovery campaign."""
    result = await db.execute(select(DiscoveryCampaign).where(DiscoveryCampaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise NotFoundError("DiscoveryCampaign", str(campaign_id))

    await db.delete(campaign)
    return success_response(data={"id": campaign_id, "deleted": True})


async def _store_lead(db: AsyncSession, collected: CollectedLead) -> Optional[uuid.UUID]:
    """Store a CollectedLead into the database. Returns lead ID or None if duplicate."""
    try:
        lead = Lead(
            company_name=collected.company_name,
            company_domain=collected.company_domain,
            company_url=collected.company_url,
            company_linkedin_url=collected.company_linkedin_url,
            company_github_url=collected.company_github_url,
            industry=collected.industry,
            description=collected.description,
            employee_count=collected.employee_count,
            employee_count_range=collected.employee_count_range,
            location_city=collected.location_city,
            location_state=collected.location_state,
            location_country=collected.location_country,
            founded_year=collected.founded_year,
            funding_total=collected.funding_total,
            funding_currency=collected.funding_currency or "USD",
            funding_rounds=collected.funding_rounds,
            tech_stack=collected.tech_stack,
            social_links=collected.social_links,
            status="discovered",
            source=collected.source,
            source_id=collected.source_id,
            source_url=collected.source_url,
        )
        db.add(lead)
        await db.flush()

        # Store source data
        if collected.raw_data:
            lead_source = LeadSource(
                lead_id=lead.id,
                source=collected.source,
                source_lead_id=collected.source_id,
                source_data=collected.raw_data,
                confidence=collected.confidence if hasattr(collected, 'confidence') else 0.5,
            )
            db.add(lead_source)

        return lead.id
    except Exception:
        return None