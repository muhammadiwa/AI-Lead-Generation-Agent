"""Outreach API endpoints — campaigns, templates, sending, tracking, personalization, A/B testing."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead, Message, MessageTemplate, OutreachCampaign, CampaignLead
from app.schemas import APIResponse
from app.core import success_response
from app.core.errors import NotFoundError
from app.outreach.sender import OutreachSender, EmailSender, LinkedInSender
from app.outreach.personalizer import personalizer
from app.outreach.sequencer import sequencer, SequenceStep
from app.outreach.ab_testing import ab_testing, ABVariant, ABTestResult
from app.outreach.tracker import tracker
from app.outreach.compliance import compliance, warmup
from app.outreach.classifier import reply_classifier, ReplySentiment
from app.outreach.whatsapp import WhatsAppSender
from app.outreach.threads_dm import ThreadsDMSender

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


# ─── Personalization ───

@router.post("/outreach/personalize", response_model=APIResponse)
async def personalize_message(
    template_id: uuid.UUID,
    lead_id: uuid.UUID,
    contact_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """Personalize a template with lead data."""
    template_result = await db.execute(select(MessageTemplate).where(MessageTemplate.id == template_id))
    template = template_result.scalar_one_or_none()
    if not template:
        raise NotFoundError("MessageTemplate", str(template_id))

    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    lead_data = {
        "company_name": lead.company_name,
        "company_domain": lead.company_domain,
        "industry": lead.industry,
        "tech_stack": lead.tech_stack,
        "description": lead.description,
        "location_city": lead.location_city,
        "location_state": lead.location_state,
        "location_country": lead.location_country,
        "tags": lead.tags,
    }

    contact_data = None
    if contact_id:
        from app.models import Contact
        contact_result = await db.execute(select(Contact).where(Contact.id == contact_id))
        contact = contact_result.scalar_one_or_none()
        if contact:
            contact_data = {
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "full_name": contact.full_name,
                "role_title": contact.role_title,
                "role": contact.role,
            }

    sender_data = {"name": "Ship Studio Team", "title": "Engineering Partner", "company": "Ship Studio", "email": "hello@shipstudio.dev"}

    result = personalizer.fill_template(
        template_body=template.body_template,
        template_subject=template.subject,
        lead_data=lead_data,
        contact_data=contact_data,
        sender_data=sender_data,
    )

    return success_response(data=result)


# ─── A/B Testing ───

@router.post("/outreach/ab-test/register", response_model=APIResponse, status_code=201)
async def register_ab_test(
    test_name: str,
    variants: list[dict],
    control_pct: float = 80,
):
    """Register an A/B test with multiple variants."""
    ab_variants = [
        ABVariant(
            name=v.get("name", f"variant_{i}"),
            subject=v.get("subject"),
            body=v.get("body"),
            channel=v.get("channel", "email"),
        )
        for i, v in enumerate(variants)
    ]
    ab_testing.register_test(test_name, ab_variants, control_pct)
    return success_response(data={"test_name": test_name, "variants": len(ab_variants)})


@router.get("/outreach/ab-test/{test_name}/results", response_model=APIResponse)
async def get_ab_test_results(test_name: str):
    """Get A/B test results."""
    results = ab_testing.get_results(test_name)
    winner = ab_testing.get_winner(test_name)
    return success_response(data={"results": results, "winner": winner})


# ─── Sequences ───

@router.get("/outreach/sequences/default", response_model=APIResponse)
async def get_default_sequence():
    """Get the default outreach sequence."""
    steps = sequencer.get_steps("default")
    return success_response(data={
        "steps": [
            {
                "day": s.day,
                "channel": s.channel,
                "action": s.action,
                "subject_variants": s.subject_variants,
                "condition": s.condition,
                "wait_for_reply": s.wait_for_reply,
            }
            for s in steps
        ]
    })


@router.post("/outreach/send-personalized", response_model=APIResponse)
async def send_personalized(
    lead_id: uuid.UUID,
    template_id: uuid.UUID,
    channel: str = "email",
    db: AsyncSession = Depends(get_db),
):
    """Personalize a template and send immediately."""
    template_result = await db.execute(select(MessageTemplate).where(MessageTemplate.id == template_id))
    template = template_result.scalar_one_or_none()
    if not template:
        raise NotFoundError("MessageTemplate", str(template_id))

    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead", str(lead_id))

    lead_data = {
        "company_name": lead.company_name,
        "company_domain": lead.company_domain,
        "industry": lead.industry,
        "tech_stack": lead.tech_stack,
        "description": lead.description,
    }
    sender_data = {"name": "Ship Studio Team", "title": "Engineering Partner", "company": "Ship Studio", "email": "hello@shipstudio.dev"}

    personalized = personalizer.fill_template(template.body_template, template.subject, lead_data, sender_data=sender_data)

    sender = OutreachSender()
    result = await sender.send(
        channel=channel,
        recipient=lead.company_name,
        subject=personalized["subject"],
        body=personalized["body"],
    )

    if result.success:
        message = Message(
            lead_id=lead_id,
            template_id=template_id,
            channel=channel,
            subject=personalized["subject"],
            body_text=personalized["body"],
            status="sent" if result.external_id else "queued",
            external_id=result.external_id,
        )
        db.add(message)
        lead.status = "contacted"
        db.add(lead)

    return success_response(data={
        "success": result.success,
        "message_id": str(message.id) if result.success else None,
        "external_id": result.external_id,
        "error": result.error,
        "personalized": personalized,
    })


# ─── Reply Classification ───

@router.post("/outreach/classify-reply", response_model=APIResponse)
async def classify_reply(
    reply_text: str = Query(..., min_length=1),
):
    """Classify a reply's sentiment."""
    result = reply_classifier.classify(reply_text)
    return success_response(data={
        "sentiment": result.sentiment.value,
        "confidence": result.confidence,
        "matched_keywords": result.matched_keywords,
        "suggested_action": result.suggested_action,
    })


# ─── Compliance ───

@router.post("/outreach/unsubscribe", response_model=APIResponse)
async def unsubscribe(
    email: str,
    campaign_id: Optional[str] = None,
):
    """Unsubscribe an email address."""
    compliance.unsubscribe(email, campaign_id)
    return success_response(data={"email": email, "status": "unsubscribed"})


@router.get("/outreach/compliance/suppression-list", response_model=APIResponse)
async def get_suppression_list():
    """Get the suppression list (GDPR export)."""
    return success_response(data={"suppressed": compliance.get_suppression_list()})


@router.get("/outreach/compliance/warmup-status", response_model=APIResponse)
async def get_warmup_status(domain: str = "shipstudio.dev"):
    """Get warm-up status for a sending domain."""
    status = warmup.get_daily_limit(domain)
    fully_warmed = warmup.is_fully_warmed(domain)
    return success_response(data={
        "domain": domain,
        "daily_limit": status,
        "fully_warmed": fully_warmed,
    })


# ─── Tracking Webhooks ───

@router.post("/webhooks/email-status", response_model=APIResponse)
async def email_status_webhook(
    event_type: str,
    message_id: str,
    email: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Webhook endpoint for email delivery status (Resend/SendGrid)."""
    tracker.record_event(message_id, event_type, metadata or {})

    if event_type == "bounced" and email:
        compliance.record_bounce(email, "hard" if metadata and metadata.get("severity") == "permanent" else "soft")

    return success_response(data={"recorded": True})


@router.get("/outreach/tracking/{message_id}", response_model=APIResponse)
async def get_tracking_detail(message_id: str):
    """Get detailed tracking for a message."""
    status = tracker.get_message_status(message_id)
    events = tracker.get_events(message_id)
    return success_response(data={"status": status, "events": events})


# ─── WhatsApp Messaging ───

@router.post("/outreach/whatsapp/send", response_model=APIResponse)
async def send_whatsapp(
    to: str,
    body: str = "",
    template_name: Optional[str] = None,
):
    """Send a WhatsApp message (text or template)."""
    sender = WhatsAppSender()
    if template_name:
        result = await sender.send_template(to, template_name, {})
    else:
        result = await sender.send_text(to, body)
    return success_response(data={
        "success": result.success,
        "channel": "whatsapp",
        "message_id": result.message_id,
        "error": result.error,
    })


@router.get("/outreach/whatsapp/status", response_model=APIResponse)
async def whatsapp_status():
    """Check WhatsApp API configuration status."""
    from app.config import settings
    configured = bool(settings.__dict__.get("whatsapp_from_number", ""))
    return success_response(data={
        "configured": configured,
        "message": "WhatsApp API configured" if configured else "WhatsApp API not configured — set WHATSAPP_FROM_NUMBER",
    })


# ─── Threads DM Messaging ───

@router.post("/outreach/threads/send", response_model=APIResponse)
async def send_threads_dm(
    to: str,
    body: str,
):
    """Send a Threads DM."""
    sender = ThreadsDMSender()
    result = await sender.send(to=to, body=body)
    return success_response(data={
        "success": result.success,
        "channel": "threads_dm",
        "message_id": result.message_id,
        "error": result.error,
    })


@router.post("/outreach/threads/sequence", response_model=APIResponse)
async def send_threads_sequence(
    to: str,
    messages: list[str],
    delay_seconds: int = 60,
):
    """Send a sequence of Threads DMs with delays."""
    sender = ThreadsDMSender()
    results = await sender.send_dm_sequence(to, messages, delay_seconds)
    return success_response(data={
        "results": [
            {"success": r.success, "error": r.error, "index": i}
            for i, r in enumerate(results)
        ],
    })


@router.get("/outreach/threads/status", response_model=APIResponse)
async def threads_status():
    """Check Threads API configuration status."""
    from app.config import settings
    configured = bool(settings.__dict__.get("threads_access_token", ""))
    return success_response(data={
        "configured": configured,
        "message": "Threads API configured" if configured else "Threads API not configured — set THREADS_ACCESS_TOKEN",
    })