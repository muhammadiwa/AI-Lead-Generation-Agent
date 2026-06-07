"""Analytics API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead, Message, Job, DailyStat
from app.schemas import APIResponse, success_response

router = APIRouter(tags=["Analytics"])


@router.get("/analytics/overview", response_model=APIResponse)
async def analytics_overview(db: AsyncSession = Depends(get_db)):
    """Dashboard summary statistics."""
    # Total leads
    total_result = await db.execute(select(func.count(Lead.id)))
    total_leads = total_result.scalar() or 0

    # Leads by status
    status_result = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )
    leads_by_status = {row[0]: row[1] for row in status_result.all()}

    # Leads by source
    source_result = await db.execute(
        select(Lead.source, func.count(Lead.id)).group_by(Lead.source)
    )
    leads_by_source = {row[0]: row[1] for row in source_result.all()}

    # Avg score
    avg_score_result = await db.execute(select(func.avg(Lead.score_current)))
    avg_score = float(avg_score_result.scalar() or 0)

    # Message stats
    sent_result = await db.execute(
        select(func.count(Message.id)).where(Message.status.in_(["sent", "delivered", "opened", "replied"]))
    )
    total_sent = sent_result.scalar() or 0

    replied_result = await db.execute(
        select(func.count(Message.id)).where(Message.status == "replied")
    )
    total_replied = replied_result.scalar() or 0

    return success_response(
        data={
            "total_leads": total_leads,
            "leads_by_status": leads_by_status,
            "leads_by_source": leads_by_source,
            "average_score": round(avg_score, 2),
            "total_messages_sent": total_sent,
            "total_replies": total_replied,
            "reply_rate": round((total_replied / total_sent * 100), 2) if total_sent > 0 else 0,
        }
    )


@router.get("/analytics/pipeline", response_model=APIResponse)
async def analytics_pipeline(db: AsyncSession = Depends(get_db)):
    """Lead pipeline funnel data."""
    status_result = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )
    pipeline = {row[0]: row[1] for row in status_result.all()}

    return success_response(data={"pipeline": pipeline})


@router.get("/analytics/sources", response_model=APIResponse)
async def analytics_sources(db: AsyncSession = Depends(get_db)):
    """Lead source attribution."""
    source_result = await db.execute(
        select(Lead.source, func.count(Lead.id)).group_by(Lead.source)
    )
    sources = {row[0]: row[1] for row in source_result.all()}

    total = sum(sources.values()) if sources else 0
    attribution = {
        source: {
            "count": count,
            "percentage": round((count / total * 100), 2) if total > 0 else 0,
        }
        for source, count in sources.items()
    }

    return success_response(data={"source_attribution": attribution})