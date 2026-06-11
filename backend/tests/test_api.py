"""Tests for API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Health check endpoint tests."""

    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"

    async def test_root_endpoint(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "Lead Gen Agent" in data["name"]


class TestLeadEndpoints:
    """Lead CRUD endpoint tests."""

    async def test_create_lead(self, client: AsyncClient):
        lead_data = {
            "company_name": "TestCorp",
            "company_domain": "testcorp.com",
            "industry": "SaaS",
            "source": "manual",
            "employee_count": 50,
        }
        resp = await client.post("/api/v1/leads", json=lead_data)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["company_name"] == "TestCorp"
        assert "id" in data["data"]

    async def test_list_leads(self, client: AsyncClient):
        # Create a lead first
        await client.post("/api/v1/leads", json={
            "company_name": "ListCorp", "source": "manual"
        })

        resp = await client.get("/api/v1/leads")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["data"]) >= 1

    async def test_get_lead_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/leads/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
        data = resp.json()
        assert data["status"] == "error"
        assert "NOT_FOUND" in data["error"]["code"]

    async def test_update_lead(self, client: AsyncClient):
        # Create
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "UpdateCorp", "source": "manual"
        })
        lead_id = create_resp.json()["data"]["id"]

        # Update
        resp = await client.patch(f"/api/v1/leads/{lead_id}", json={
            "company_name": "UpdatedCorp",
            "notes": "Updated via test"
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["company_name"] == "UpdatedCorp"

    async def test_delete_lead(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "DeleteCorp", "source": "manual"
        })
        lead_id = create_resp.json()["data"]["id"]

        resp = await client.delete(f"/api/v1/leads/{lead_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "archived"


class TestDiscoveryEndpoints:
    """Discovery endpoint tests."""

    async def test_discovery_search(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/discovery/search",
            json={
                "sources": ["crunchbase", "github"],
                "max_leads": 10,
                "config": {},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

    async def test_create_discovery_campaign(self, client: AsyncClient):
        # First create an ICP profile
        icp_resp = await client.post("/api/v1/icp", json={
            "name": "Test ICP",
            "filters": [],
        })
        icp_id = icp_resp.json()["data"]["id"]

        resp = await client.post(
            "/api/v1/discovery/campaigns",
            json={
                "name": "Test Campaign",
                "icp_profile_id": icp_id,
                "sources": ["github", "crunchbase"],
                "config": {"topics": ["python"]},
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "Test Campaign"


class TestScoringEndpoints:
    """Scoring endpoint tests."""

    async def test_recalculate_scores(self, client: AsyncClient):
        # Create a lead with data
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "ScoreCorp",
            "source": "manual",
            "industry": "SaaS",
            "employee_count": 100,
        })

        resp = await client.post("/api/v1/scoring/recalculate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["recalculated"] >= 1


class TestICPEndpoints:
    """ICP profile endpoint tests."""

    async def test_create_icp_profile(self, client: AsyncClient):
        resp = await client.post("/api/v1/icp", json={
            "name": "SaaS Companies",
            "description": "Companies in the SaaS space",
            "filters": [
                {
                    "filter_type": "industry",
                    "filter_key": "industry",
                    "filter_value": ["SaaS", "software"],
                    "operator": "in",
                    "weight": 20,
                }
            ],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["name"] == "SaaS Companies"

    async def test_list_icp_profiles(self, client: AsyncClient):
        resp = await client.get("/api/v1/icp")
        assert resp.status_code == 200


class TestAnalyticsEndpoints:
    """Analytics endpoint tests."""

    async def test_analytics_overview(self, client: AsyncClient):
        resp = await client.get("/api/v1/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "total_leads" in data["data"]


class TestOutreachEndpoints:
    """Outreach endpoint tests."""

    async def test_create_template(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/outreach/templates",
            params={
                "name": "Cold Email Template",
                "channel": "email",
                "subject": "Quick thought about {{company_name}}",
                "body_template": "Hi {{name}},\n\nI noticed {{company_name}} is...",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["name"] == "Cold Email Template"

    async def test_create_campaign(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/outreach/campaigns",
            params={
                "name": "Q1 Campaign",
                "channels": ["email"],
                "auto_send": False,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "Q1 Campaign"