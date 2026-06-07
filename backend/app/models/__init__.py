"""SQLAlchemy models for the Lead Gen Agent database."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ICPProfile(Base):
    __tablename__ = "icp_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    filters = relationship("ICPFilter", back_populates="icp_profile", cascade="all, delete-orphan")
    discovery_campaigns = relationship("DiscoveryCampaign", back_populates="icp_profile")


class ICPFilter(Base):
    __tablename__ = "icp_filters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    icp_profile_id = Column(UUID(as_uuid=True), ForeignKey("icp_profiles.id", ondelete="CASCADE"), nullable=False)
    filter_type = Column(String(50), nullable=False)
    filter_key = Column(String(255), nullable=False)
    filter_value = Column(JSONB, nullable=False)
    operator = Column(String(20), default="in")
    weight = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    icp_profile = relationship("ICPProfile", back_populates="filters")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(512), nullable=False)
    company_domain = Column(String(255), nullable=True)
    company_url = Column(String(1024), nullable=True)
    company_linkedin_url = Column(String(1024), nullable=True)
    company_github_url = Column(String(1024), nullable=True)
    industry = Column(String(255), nullable=True)
    industry_details = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    employee_count = Column(Integer, nullable=True)
    employee_count_range = Column(String(50), nullable=True)
    revenue_estimate = Column(JSONB, nullable=True)
    location_city = Column(String(255), nullable=True)
    location_state = Column(String(255), nullable=True)
    location_country = Column(String(100), nullable=True)
    founded_year = Column(Integer, nullable=True)
    funding_total = Column(Numeric(15, 2), nullable=True)
    funding_currency = Column(String(10), default="USD")
    funding_rounds = Column(JSONB, nullable=True)
    tech_stack = Column(JSONB, nullable=True)
    social_links = Column(JSONB, nullable=True)
    status = Column(String(50), default="discovered")
    source = Column(String(50), nullable=False)
    source_id = Column(String(255), nullable=True)
    source_url = Column(String(1024), nullable=True)
    score_current = Column(Numeric(5, 2), nullable=True)
    score_breakdown = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=True)
    custom_fields = Column(JSONB, default=dict)
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text, nullable=True)
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    icp_profile_id = Column(UUID(as_uuid=True), ForeignKey("icp_profiles.id", ondelete="SET NULL"), nullable=True)

    contacts = relationship("Contact", back_populates="lead", cascade="all, delete-orphan")
    lead_sources = relationship("LeadSource", back_populates="lead", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="lead")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    full_name = Column(String(512), nullable=True)
    email = Column(String(512), nullable=True)
    email_verified = Column(Boolean, default=False)
    email_source = Column(String(100), nullable=True)
    phone = Column(String(100), nullable=True)
    linkedin_url = Column(String(1024), nullable=True)
    github_username = Column(String(255), nullable=True)
    twitter_handle = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    role_title = Column(String(255), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    department = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String(1024), nullable=True)
    location = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)
    is_decision_maker = Column(Boolean, default=False)
    score = Column(Numeric(5, 2), nullable=True)
    engagement_score = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)
    custom_fields = Column(JSONB, default=dict)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lead = relationship("Lead", back_populates="contacts")


class LeadSource(Base):
    __tablename__ = "lead_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(50), nullable=False)
    source_lead_id = Column(String(255), nullable=True)
    source_data = Column(JSONB, nullable=True)
    raw_response = Column(JSONB, nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    synced_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="lead_sources")


class DiscoveryCampaign(Base):
    __tablename__ = "discovery_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    icp_profile_id = Column(UUID(as_uuid=True), ForeignKey("icp_profiles.id", ondelete="CASCADE"), nullable=False)
    sources = Column(ARRAY(String), default=lambda: ["linkedin", "github", "crunchbase", "web_scrape"])
    schedule_cron = Column(String(100), nullable=True)
    max_leads_per_run = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    total_leads_discovered = Column(Integer, default=0)
    config = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    icp_profile = relationship("ICPProfile", back_populates="discovery_campaigns")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    priority = Column(Integer, default=5)
    payload = Column(JSONB, nullable=False)
    result = Column(JSONB, nullable=True)
    error = Column(JSONB, nullable=True)
    progress = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    worker_id = Column(String(255), nullable=True)
    execution_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="SET NULL"), nullable=True)
    campaign_lead_id = Column(UUID(as_uuid=True), ForeignKey("campaign_leads.id", ondelete="SET NULL"), nullable=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True)
    channel = Column(String(50), nullable=False)
    subject = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    sender_email = Column(String(255), nullable=True)
    sender_name = Column(String(255), nullable=True)
    recipient_email = Column(String(512), nullable=True)
    recipient_name = Column(String(512), nullable=True)
    status = Column(String(50), default="draft")
    external_id = Column(String(512), nullable=True)
    external_data = Column(JSONB, nullable=True)
    tracking_data = Column(JSONB, default=dict)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    reply_content = Column(Text, nullable=True)
    reply_sentiment = Column(String(50), nullable=True)
    sequence_step = Column(Integer, default=1)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lead = relationship("Lead", back_populates="messages")


class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    icp_profile_id = Column(UUID(as_uuid=True), ForeignKey("icp_profiles.id"), nullable=True)
    channels = Column(ARRAY(String), default=lambda: ["email"])
    max_leads = Column(Integer, nullable=True)
    leads_processed = Column(Integer, default=0)
    auto_send = Column(Boolean, default=False)
    schedule_config = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class CampaignLead(Base):
    __tablename__ = "campaign_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    status = Column(String(50), default="draft")
    score_at_add = Column(Numeric(5, 2), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    first_reply_at = Column(DateTime(timezone=True), nullable=True)
    meeting_booked = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)
    subject = Column(Text, nullable=True)
    body_template = Column(Text, nullable=False)
    variables = Column(ARRAY(Text), nullable=True)
    variant_group = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    performance = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ScoringConfig(Base):
    __tablename__ = "scoring_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    weights = Column(JSONB, nullable=False)
    thresholds = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id"), nullable=True)
    properties = Column(JSONB, default=dict)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())


class DailyStat(Base):
    __tablename__ = "daily_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(timezone=True), nullable=False)
    leads_discovered = Column(Integer, default=0)
    leads_enriched = Column(Integer, default=0)
    leads_scored = Column(Integer, default=0)
    leads_qualified_hot = Column(Integer, default=0)
    leads_qualified_warm = Column(Integer, default=0)
    leads_cold = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    messages_opened = Column(Integer, default=0)
    messages_replied = Column(Integer, default=0)
    meetings_booked = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    jobs_completed = Column(Integer, default=0)
    jobs_failed = Column(Integer, default=0)
    source_breakdown = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())