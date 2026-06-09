"""Enhanced reporting & analytics — conversion funnel, time-series, campaign performance."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead, Message, OutreachCampaign, CampaignLead, AnalyticsEvent, DailyStat, Job
from app.schemas import APIResponse
from app.core import success_response

router = APIRouter(tags=["Reporting"])


@router.get("/reporting/conversion-funnel", response_model=APIResponse)
async def conversion_funnel(db: AsyncSession = Depends(get_db)):
    """Get the full lead conversion funnel with drop-off rates."""
    total = await db.execute(select(func.count(Lead.id)))
    total_leads = total.scalar() or 0

    stages = [
        ("discovered", "Leads Discovered"),
        ("researched", "Leads Researched"),
        ("scored", "Leads Scored"),
        ("qualified_hot", "Qualified Hot"),
        ("contacted", "Contacted"),
        ("responded", "Responded"),
        ("meeting_scheduled", "Meeting Scheduled"),
        ("converted", "Converted"),
    ]

    funnel = []
    previous_count = total_leads

    for status_key, label in stages:
        result = await db.execute(
            select(func.count(Lead.id)).where(Lead.status == status_key)
        )
        count = result.scalar() or 0

        drop_off = previous_count - count if previous_count > 0 else 0
        conversion_rate = round((count / total_leads * 100), 2) if total_leads > 0 else 0
        stage_conversion = round((count / previous_count * 100), 2) if previous_count > 0 else 0

        funnel.append({
            "stage": status_key,
            "label": label,
            "count": count,
            "conversion_rate": conversion_rate,
            "stage_conversion": stage_conversion,
            "drop_off": drop_off,
        })

        previous_count = count

    return success_response(data={
        "funnel": funnel,
        "total_leads": total_leads,
        "overall_conversion": funnel[-1]["conversion_rate"] if funnel else 0,
    })


@router.get("/reporting/time-series", response_model=APIResponse)
async def time_series_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get time-series analytics for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Leads over time
    leads_over_time = await db.execute(
        select(
            func.date(Lead.created_at).label("date"),
            func.count(Lead.id).label("count"),
        ).where(Lead.created_at >= since)
        .group_by(func.date(Lead.created_at))
        .order_by(func.date(Lead.created_at))
    )

    # Messages over time
    messages_over_time = await db.execute(
        select(
            func.date(Message.sent_at).label("date"),
            func.count(Message.id).label("count"),
        ).where(Message.sent_at >= since)
        .group_by(func.date(Message.sent_at))
        .order_by(func.date(Message.sent_at))
    )

    # Events over time
    events_over_time = await db.execute(
        select(
            func.date(AnalyticsEvent.occurred_at).label("date"),
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label("count"),
        ).where(AnalyticsEvent.occurred_at >= since)
        .group_by(func.date(AnalyticsEvent.occurred_at), AnalyticsEvent.event_type)
        .order_by(func.date(AnalyticsEvent.occurred_at))
    )

    # Build daily time series
    daily_data = {}
    for i in range(days):
        day = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).date()
        daily_data[day.isoformat()] = {"leads": 0, "messages": 0, "events": {}}

    for row in leads_over_time.all():
        day = str(row.date) if hasattr(row, 'date') else str(row[0])
        if day in daily_data:
            daily_data[day]["leads"] = row.count if hasattr(row, 'count') else row[1]

    for row in messages_over_time.all():
        day = str(row.date) if hasattr(row, 'date') else str(row[0])
        if day in daily_data:
            daily_data[day]["messages"] = row.count if hasattr(row, 'count') else row[1]

    for row in events_over_time.all():
        day = str(row.date) if hasattr(row, 'date') else str(row[0])
        event_type = row.event_type if hasattr(row, 'event_type') else row[1]
        count = row.count if hasattr(row, 'count') else row[2]
        if day in daily_data:
            daily_data[day]["events"][event_type] = count

    return success_response(data={
        "period_days": days,
        "daily": daily_data,
    })


@router.get("/reporting/campaigns", response_model=APIResponse)
async def campaign_reporting(db: AsyncSession = Depends(get_db)):
    """Get performance metrics for all outreach campaigns."""
    campaigns_result = await db.execute(
        select(OutreachCampaign).order_by(OutreachCampaign.created_at.desc())
    )
    campaigns = campaigns_result.scalars().all()

    report = []
    for campaign in campaigns:
        # Lead count for campaign
        lead_count = await db.execute(
            select(func.count(CampaignLead.id))
            .where(CampaignLead.campaign_id == campaign.id)
        )
        total_leads = lead_count.scalar() or 0

        # Message stats
        message_stats = await db.execute(
            select(
                func.count(Message.id),
                func.sum(case((Message.status == "sent", 1), else_=0)),
                func.sum(case((Message.status == "opened", 1), else_=0)),
                func.sum(case((Message.status == "replied", 1), else_=0)),
                func.sum(case((Message.status == "bounced", 1), else_=0)),
            ).where(Message.campaign_id == campaign.id)
        )
        row = message_stats.one()
        total_msgs = row[0] or 0
        sent = row[1] or 0
        opened = row[2] or 0
        replied = row[3] or 0
        bounced = row[4] or 0

        report.append({
            "id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status,
            "total_leads": total_leads,
            "total_messages": total_msgs,
            "sent": sent,
            "opened": opened,
            "open_rate": round((opened / sent * 100), 2) if sent > 0 else 0,
            "replied": replied,
            "reply_rate": round((replied / sent * 100), 2) if sent > 0 else 0,
            "bounced": bounced,
            "bounce_rate": round((bounced / sent * 100), 2) if sent > 0 else 0,
            "leads_processed": campaign.leads_processed,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        })

    return success_response(data={"campaigns": report})


@router.get("/reporting/outreach", response_model=APIResponse)
async def outreach_reporting(db: AsyncSession = Depends(get_db)):
    """Get overall outreach performance metrics."""
    total = await db.execute(select(func.count(Message.id)))
    total_msgs = total.scalar() or 0

    by_status = await db.execute(
        select(Message.status, func.count(Message.id)).group_by(Message.status)
    )
    status_counts = {row[0]: row[1] for row in by_status.all()}

    by_channel = await db.execute(
        select(Message.channel, func.count(Message.id)).group_by(Message.channel)
    )
    channel_counts = {row[0]: row[1] for row in by_channel.all()}

    sent = status_counts.get("sent", 0)
    opened = status_counts.get("opened", 0)
    replied = status_counts.get("replied", 0)
    bounced = status_counts.get("bounced", 0)

    return success_response(data={
        "total_messages": total_msgs,
        "by_status": status_counts,
        "by_channel": channel_counts,
        "metrics": {
            "sent": sent,
            "opened": opened,
            "open_rate": round((opened / sent * 100), 2) if sent > 0 else 0,
            "replied": replied,
            "reply_rate": round((replied / sent * 100), 2) if sent > 0 else 0,
            "bounced": bounced,
            "bounce_rate": round((bounced / sent * 100), 2) if sent > 0 else 0,
        },
    })


@router.get("/reporting/jobs", response_model=APIResponse)
async def job_reporting(db: AsyncSession = Depends(get_db)):
    """Get job processing metrics."""
    total = await db.execute(select(func.count(Job.id)))
    total_jobs = total.scalar() or 0

    by_type = await db.execute(
        select(Job.type, func.count(Job.id)).group_by(Job.type)
    )
    type_counts = {row[0]: row[1] for row in by_type.all()}

    by_status = await db.execute(
        select(Job.status, func.count(Job.id)).group_by(Job.status)
    )
    status_counts = {row[0]: row[1] for row in by_status.all()}

    avg_duration = await db.execute(
        select(func.avg(Job.execution_ms)).where(Job.status == "completed")
    )
    avg_ms = avg_duration.scalar()

    return success_response(data={
        "total_jobs": total_jobs,
        "by_type": type_counts,
        "by_status": status_counts,
        "average_execution_ms": round(float(avg_ms), 2) if avg_ms else 0,
        "success_rate": round(
            (status_counts.get("completed", 0) / total_jobs * 100), 2
        ) if total_jobs > 0 else 0,
    })