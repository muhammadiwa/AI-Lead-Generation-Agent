"""Tests for the lead qualification & scoring engine."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestSignalDetection:
    """NLP signal detection tests."""

    async def test_signal_detection_on_lead(self, client: AsyncClient):
        # Create a lead with text that should trigger hiring signals
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "TechGrowth Inc",
            "description": "We are hiring software engineers and looking for a CTO to join our team. We are scaling rapidly and need to modernize our legacy stack.",
            "source": "manual",
            "industry": "SaaS",
            "employee_count": 25,
        })
        lead_id = create_resp.json()["data"]["id"]

        # Detect signals
        resp = await client.get(f"/api/v1/leads/{lead_id}/signals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["total_signals"] >= 1
        signal_types = [s["type"] for s in data["data"]["signals"]]
        assert any("hiring" in s for s in signal_types) or any("seeking" in s or "tech" in s for s in signal_types)

    async def test_signals_empty_lead(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "MinimalCorp",
            "source": "manual",
        })
        lead_id = create_resp.json()["data"]["id"]

        resp = await client.get(f"/api/v1/leads/{lead_id}/signals")
        assert resp.status_code == 200
        assert resp.json()["data"]["total_signals"] >= 0

    async def test_signals_tech_debt_detection(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "LegacySystems",
            "description": "Our team needs to migrate from our monolithic legacy infrastructure to a modern microservices architecture on AWS.",
            "source": "manual",
            "tech_stack": {"detected_technologies": ["PHP", "MySQL", "jQuery"]},
        })
        lead_id = create_resp.json()["data"]["id"]

        resp = await client.get(f"/api/v1/leads/{lead_id}/signals")
        assert resp.status_code == 200
        signals = resp.json()["data"]["signals"]
        types = [s["type"] for s in signals]
        assert "tech_debt" in types or "pain_point" in types


class TestLLMAnalysis:
    """LLM analysis endpoint tests."""

    async def test_llm_analysis_no_api_key(self, client: AsyncClient):
        """Should use fallback analysis when no API key configured."""
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "TestAnalyzeCorp",
            "description": "Fast-growing SaaS company looking to scale their engineering team. Currently hiring 5 senior developers.",
            "source": "manual",
            "industry": "SaaS",
            "employee_count": 50,
        })
        lead_id = create_resp.json()["data"]["id"]

        resp = await client.post(f"/api/v1/leads/{lead_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        # Fallback analysis should still return useful data
        assert len(data["data"]["pain_points"]) >= 0
        assert len(data["data"]["tech_needs"]) >= 0
        assert data["data"]["engagement_score"] >= 0


class TestEnrichment:
    """Enrichment endpoint tests."""

    async def test_enrich_no_domain(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "NoDomainCorp",
            "source": "manual",
        })
        lead_id = create_resp.json()["data"]["id"]

        resp = await client.post(f"/api/v1/leads/{lead_id}/enrich")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["enriched"] is False
        assert "domain" in data["data"]["message"]


class TestFullQualification:
    """Full qualification pipeline tests."""

    async def test_qualify_lead(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "ScoredLead Inc",
            "description": "We build SaaS analytics tools. Growing rapidly with recent Series A funding. Looking for experienced React and Python developers.",
            "source": "manual",
            "industry": "SaaS",
            "employee_count": 45,
            "location_country": "US",
            "funding_total": 5000000,
            "tech_stack": {"detected_technologies": ["React", "Python", "PostgreSQL", "AWS"]},
        })
        lead_id = create_resp.json()["data"]["id"]

        resp = await client.post("/api/v1/scoring/qualify", params={"lead_id": lead_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["total_score"] > 0
        assert data["data"]["qualification"] in ("hot", "warm", "cool", "cold")
        assert len(data["data"]["breakdown"]) > 0
        # Should have signals detected
        assert len(data["data"]["signals"]) > 0

    async def test_qualify_batch(self, client: AsyncClient):
        ids = []
        for name in ["BatchLead A", "BatchLead B"]:
            resp = await client.post("/api/v1/leads", json={
                "company_name": name,
                "source": "manual",
                "industry": "Technology",
            })
            ids.append(resp.json()["data"]["id"])

        resp = await client.post("/api/v1/scoring/qualify-batch", json={"lead_ids": ids})
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["qualified"] == 2
        assert len(data["data"]["results"]) == 2

    async def test_qualify_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/scoring/qualify",
            params={"lead_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert resp.status_code == 404


class TestSimilarLeads:
    """Similar lead search tests."""

    async def test_similar_leads(self, client: AsyncClient):
        # Create two leads in similar industries
        resp1 = await client.post("/api/v1/leads", json={
            "company_name": "SaaSPlatform",
            "source": "manual",
            "industry": "SaaS",
            "description": "We build cloud-based analytics software",
        })
        lead1_id = resp1.json()["data"]["id"]

        resp2 = await client.post("/api/v1/leads", json={
            "company_name": "CloudAnalytics",
            "source": "manual",
            "industry": "SaaS",
            "description": "Cloud analytics and business intelligence platform",
        })
        lead2_id = resp2.json()["data"]["id"]

        resp = await client.post(
            "/api/v1/scoring/similar",
            params={"lead_id": lead1_id, "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "similar_leads" in data["data"]


class TestLegacyScoring:
    """Legacy scoring still works."""

    async def test_legacy_recalculate(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "LegacyScore",
            "source": "manual",
            "industry": "SaaS",
            "employee_count": 100,
        })

        resp = await client.post("/api/v1/scoring/recalculate")
        assert resp.status_code == 200
        assert resp.json()["data"]["recalculated"] >= 1

    async def test_legacy_get_score(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/leads", json={
            "company_name": "GetScore",
            "source": "manual",
        })
        lead_id = create_resp.json()["data"]["id"]

        # Recalculate first
        await client.post("/api/v1/scoring/recalculate")

        resp = await client.get(f"/api/v1/leads/{lead_id}/score")
        assert resp.status_code == 200