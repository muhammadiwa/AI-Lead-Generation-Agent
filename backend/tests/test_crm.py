"""Tests for CRM, pipeline, job monitoring, webhooks, and reporting APIs."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestPipelineAPI:
    """Pipeline management tests."""

    async def test_get_pipeline(self, client: AsyncClient):
        resp = await client.get("/api/v1/pipeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "pipeline" in data["data"]

    async def test_get_pipeline_stage(self, client: AsyncClient):
        resp = await client.get("/api/v1/pipeline/discovered/leads")
        assert resp.status_code == 200
        assert resp.json()["data"]["stage"] == "discovered"

    async def test_move_lead_stage(self, client: AsyncClient):
        create = await client.post("/api/v1/leads", json={
            "company_name": "MoveTest", "source": "manual"
        })
        lead_id = create.json()["data"]["id"]

        resp = await client.post(
            f"/api/v1/pipeline/{lead_id}/move",
            params={"target_stage": "researched"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["current_stage"] == "researched"

    async def test_bulk_move(self, client: AsyncClient):
        ids = []
        for name in ["BulkA", "BulkB"]:
            r = await client.post("/api/v1/leads", json={"company_name": name, "source": "manual"})
            ids.append(r.json()["data"]["id"])

        resp = await client.post("/api/v1/pipeline/bulk-move", json={
            "lead_ids": ids, "target_stage": "contacted"
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["moved"] == 2


class TestJobMonitoring:
    """Job monitoring tests."""

    async def test_list_jobs(self, client: AsyncClient):
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        assert "jobs" in resp.json()["data"]

    async def test_job_stats(self, client: AsyncClient):
        resp = await client.get("/api/v1/jobs/stats")
        assert resp.status_code == 200


class TestWebhookSystem:
    """Webhook registration and management tests."""

    async def test_register_webhook(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/webhooks/register",
            params={
                "url": "https://hooks.slack.com/services/test",
                "events": ["lead.discovered", "lead.qualified"],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data["data"]
        assert data["data"]["url"] == "https://hooks.slack.com/services/test"

    async def test_list_webhooks(self, client: AsyncClient):
        resp = await client.get("/api/v1/webhooks/registrations")
        assert resp.status_code == 200
        assert "webhooks" in resp.json()["data"]


class TestReporting:
    """Enhanced reporting tests."""

    async def test_conversion_funnel(self, client: AsyncClient):
        resp = await client.get("/api/v1/reporting/conversion-funnel")
        assert resp.status_code == 200
        assert "funnel" in resp.json()["data"]

    async def test_time_series(self, client: AsyncClient):
        resp = await client.get("/api/v1/reporting/time-series?days=7")
        assert resp.status_code == 200
        assert "daily" in resp.json()["data"]

    async def test_outreach_reporting(self, client: AsyncClient):
        resp = await client.get("/api/v1/reporting/outreach")
        assert resp.status_code == 200
        assert "metrics" in resp.json()["data"]

    async def test_job_reporting(self, client: AsyncClient):
        resp = await client.get("/api/v1/reporting/jobs")
        assert resp.status_code == 200
        assert "total_jobs" in resp.json()["data"]