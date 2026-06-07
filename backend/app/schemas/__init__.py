"""Pydantic schemas for request/response validation."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Standard API Response Envelope ───

class APIResponse(BaseModel):
    status: str = "success"
    data: Any = None
    meta: Optional[Dict[str, Any]] = None


class APIError(BaseModel):
    code: str
    message: str
    details: Any = None


class APIErrorResponse(BaseModel):
    status: str = "error"
    error: APIError


# ─── Lead Schemas ───

class LeadCreate(BaseModel):
    company_name: str
    company_domain: Optional[str] = None
    company_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_github_url: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    founded_year: Optional[int] = None
    source: str
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    tech_stack: Optional[Dict[str, Any]] = None
    social_links: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    icp_profile_id: Optional[uuid.UUID] = None


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_github_url: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    founded_year: Optional[int] = None
    funding_total: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    is_blacklisted: Optional[bool] = None
    blacklist_reason: Optional[str] = None


class LeadResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    company_domain: Optional[str] = None
    company_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    founded_year: Optional[int] = None
    funding_total: Optional[float] = None
    tech_stack: Optional[Dict[str, Any]] = None
    social_links: Optional[Dict[str, Any]] = None
    status: str
    source: str
    score_current: Optional[float] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_blacklisted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    limit: int


# ─── Contact Schemas ───

class ContactCreate(BaseModel):
    lead_id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: Optional[str] = None
    role_title: Optional[str] = None
    is_primary: bool = False
    is_decision_maker: bool = False


class ContactResponse(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    email_verified: bool
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: Optional[str] = None
    role_title: Optional[str] = None
    is_primary: bool
    is_decision_maker: bool

    model_config = {"from_attributes": True}


# ─── ICP Schemas ───

class ICPFilterCreate(BaseModel):
    filter_type: str
    filter_key: str
    filter_value: Any
    operator: str = "in"
    weight: int = 10


class ICPProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None
    filters: List[ICPFilterCreate] = []


class ICPProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Discovery Schemas ───

class DiscoverySearchRequest(BaseModel):
    icp_profile_id: Optional[uuid.UUID] = None
    sources: List[str] = ["linkedin", "github", "crunchbase"]
    max_leads: int = 50
    config: Dict[str, Any] = {}


class DiscoveryCampaignCreate(BaseModel):
    name: str
    icp_profile_id: uuid.UUID
    sources: List[str] = ["linkedin", "github", "crunchbase", "web_scrape"]
    schedule_cron: Optional[str] = None
    max_leads_per_run: int = 100
    config: Dict[str, Any]


class DiscoveryCampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    icp_profile_id: uuid.UUID
    sources: List[str]
    schedule_cron: Optional[str] = None
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    total_leads_discovered: int

    model_config = {"from_attributes": True}


# ─── Scoring Schemas ───

class ScoringWeightsUpdate(BaseModel):
    icp_fit: int = 30
    tech_signal: int = 25
    budget_indicator: int = 20
    engagement_potential: int = 15
    urgency: int = 10


class LeadScoreResponse(BaseModel):
    lead_id: uuid.UUID
    total_score: float
    breakdown: Dict[str, Any]
    qualification: str


# ─── Health Check ───

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"