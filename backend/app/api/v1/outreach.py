"""Outreach API endpoints — campaigns, templates, sending, tracking."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead, Message, MessageTemplate, OutreachCampaign, CampaignLead
from app.schemas import APIResponse, success_response
from app.core.errors import NotFoundError

router = APIRouter(tags=["Outreach"])


# ─── Campaigns ───

@router.post("/outreach/campaigns", response_model=APIResponse, status_code=201)
async def create_outreach_campaign(
    name: str,
    description: Optional[str] = None,
    channels: list[str] = ["email"],
    auto_send: bool = False,
    icp_profile_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """Create an outreach campaign."""
    campaign = OutreachCampaign(
        name=name,
        description=description,
        channels=channels,
        auto_send=auto_send,
        icp_profile_id=icp_profile_id,
    )
    db.add(campaign)
    await db.flush()

    return success_response(data={"id": campaign.id, "name": campaign.name}, meta={"created": True})


@router.get("/outreach/campaigns", response_model=APIResponse)
async def list_outreach_campaigns(db: AsyncSession = Depends(get_db)):
    """List all outreach campaigns."""
    result = await db.execute(select(OutreachCampaign).order_by(OutreachCampaign.created_at.desc()))
    campaigns = result.scalars().all()

    return success_response(
        data=[
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "channels": c.channels,
                "leads_processed": c.leads_processed,
                "auto_send": c.auto_send,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in campaigns
        ]
    )


# ─── Templates ───

@router.post("/outreach/templates", response_model=APIResponse, status_code=201)
async def create_template(
    name: str,
    channel: str = "email",
    subject: Optional[str] = None,
    body_template: str = "",
    campaign_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a message template."""
    template = MessageTemplate(
        name=name,
        channel=channel,
        subject=subject,
        body_template=body_template,
        campaign_id=campaign_id,
    )
    db.add(template)
    await db.flush()

    return success_response(data={"id": template.id, "name": template.name})


@router.get("/outreach/templates", response_model=APIResponse)
async def list_templates(db: AsyncSession = Depends(get_db)):
    """List all message templates."""
    result = await db.execute(select(MessageTemplate).where(MessageTemplate.is_active == True))
    templates = result.scalars().all()

    return success_response(
        data=[
            {
                "id": t.id,
                "name": t.name,
                "channel": t.channel,
                "subject": t.subject,
                "variant_group": t.variant_group,
            }
            for t in templates
        ]
    )


@router.patch("/outreach/templates/{template_id}", response_model=APIResponse)
async def update_template(
    template_id: uuid.UUID,
    name: Optional[str] = None,
    body_template: Optional[str] = None,
    subject: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update a template."""
    result = await db.execute(select(MessageTemplate).where(MessageTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise NotFoundError("MessageTemplate", str(template_id))

    if name:
        template.name = name
    if body_template:
        template.body_template = body_template
    if subject:
        template.subject = subject
    if is_active is not None:
        template.is_active = is_active

    db.add(template)
    return success_response(data={"id": template.id, "updated": True})


# ─── Sending ───

@router.post("/outreach/send", response_model=APIResponse)
async def send_outreach(
    lead_id: uuid.UUID,
    template_id: uuid.UUID,
    channel: str = "email",
    db: AsyncSession = Depends(get_db),
):
    """Send an immediate outreach message to a lead."""
    # Get lead
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    # Get template
    template_result = await db.execute(select(MessageTemplate).where(MessageTemplate.id == template_id))
    template = template_result.scalar_one_or_none()
    if not template:
        raise NotFoundError("MessageTemplate", str(template_id))

    # Create message record (queued for sending)
    message = Message(
        lead_id=lead_id,
        template_id=template_id,
        channel=channel,
        subject=template.subject,
        body_text=template.body_template,
        status="queued",
    )
    db.add(message)

    # Update lead status
    lead.status = "contacted"
    lead.last_contacted_at = None  # Will be set when actually sent
    db.add(lead)

    return success_response(data={"message_id": message.id, "status": "queued"})


@router.post("/outreach/schedule", response_model=APIResponse)
async def schedule_outreach(
    lead_id: uuid.UUID,
    template_id: uuid.UUID,
    scheduled_for: str,  # ISO datetime string
    channel: str = "email",
    db: AsyncSession = Depends(get_db),
):
    """Schedule future outreach."""
    from datetime import datetime

    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    message = Message(
        lead_id=lead_id,
        template_id=template_id,
        channel=channel,
        status="draft",
        scheduled_for=datetime.fromisoformat(scheduled_for) if scheduled_for else None,
    )
    db.add(message)

    return success_response(data={"message_id": message.id, "status": "scheduled"})


# ─── Tracking ───

@router.get("/outreach/{message_id}/tracking", response_model=APIResponse)
async def get_message_tracking(message_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get message engagement data."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise NotFoundError("Message", str(message_id))

    return success_response(
        data={
            "id": message.id,
            "status": message.status,
            "channel": message.channel,
            "opened_at": message.opened_at.isoformat() if message.opened_at else None,
            "clicked_at": message.clicked_at.isoformat() if message.clicked_at else None,
            "replied_at": message.replied_at.isoformat() if message.replied_at else None,
            "reply_sentiment": message.reply_sentiment,
            "sequence_step": message.sequence_step,
            "tracking_data": message.tracking_data,
        }
    )