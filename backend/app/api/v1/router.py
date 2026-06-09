"""API v1 router — aggregates all endpoint modules."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.leads import router as leads_router
from app.api.v1.discovery import router as discovery_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.outreach import router as outreach_router
from app.api.v1.icp import router as icp_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.reporting import router as reporting_router

router = APIRouter(prefix="/api/v1")

router.include_router(leads_router)
router.include_router(discovery_router)
router.include_router(scoring_router)
router.include_router(outreach_router)
router.include_router(icp_router)
router.include_router(analytics_router)
router.include_router(pipeline_router)
router.include_router(jobs_router)
router.include_router(webhooks_router)
router.include_router(reporting_router)