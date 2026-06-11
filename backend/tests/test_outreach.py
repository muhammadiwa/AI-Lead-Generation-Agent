"""Tests for the outreach automation engine."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestPersonalization:
    """Template personalization tests."""

    async def test_personalize_template(self, client: AsyncClient):
        # Create a template with variables
        tmpl_resp = await client.post(
            "/api/v1/outreach/templates",
            params={
                "name": "Cold Email",
                "channel": "email",
                "subject": "Quick thought on {{company_name}}'s {{tech}}",
                "body_template": "Hi {{first_name}}, I noticed {{company_name}} uses {{tech_stack}}.",
            },
        )
        tmpl_id = tmpl_resp.json()["data"]["id"]

        # Create a lead
        lead_resp = await client.post("/api/v1/leads", json={
            "company_name": "TestCorp",
            "company_domain": "testcorp.com",
            "industry": "SaaS",
            "tech_stack": {"detected_technologies": ["React", "Python", "AWS"]},
            "source": "manual",
        })
        lead_id = lead_resp.json()["data"]["id"]

        # Personalize
        resp = await client.post(
            f"/api/v1/outreach/personalize",
            params={"template_id": tmpl_id, "lead_id": lead_id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "TestCorp" in data["data"]["subject"]
        assert "React" in data["data"]["body"]


class TestReplyClassifier:
    """Reply classification tests."""

    async def test_classify_positive(self, client: AsyncClient):
        resp = await client.post("/api/v1/outreach/classify-reply", params={"reply_text": "Yes, I'm interested! Let's talk."})
        assert resp.status_code == 200
        assert resp.json()["data"]["sentiment"] == "positive"

    async def test_classify_negative(self, client: AsyncClient):
        resp = await client.post("/api/v1/outreach/classify-reply", params={"reply_text": "Not interested. Remove me from your list."})
        assert resp.status_code == 200
        assert resp.json()["data"]["sentiment"] == "negative"

    async def test_classify_neutral(self, client: AsyncClient):
        resp = await client.post("/api/v1/outreach/classify-reply", params={"reply_text": "Not now, maybe later. Send me more info."})
        assert resp.status_code == 200
        assert resp.json()["data"]["sentiment"] == "neutral"


class TestABTesting:
    """A/B testing endpoint tests."""

    async def test_register_ab_test(self, client: AsyncClient):
        resp = await client.post("/api/v1/outreach/ab-test/register", json={
            "test_name": "subject_line_test",
            "variants": [
                {"name": "tech_angle", "subject": "{{company_name}}'s {{tech}} setup", "channel": "email"},
                {"name": "hiring_angle", "subject": "Noticed {{company_name}} is hiring", "channel": "email"},
            ],
            "control_pct": 80,
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["variants"] == 2

    async def test_get_ab_test_results(self, client: AsyncClient):
        resp = await client.get("/api/v1/outreach/ab-test/subject_line_test/results")
        assert resp.status_code == 200


class TestCompliance:
    """Compliance endpoint tests."""

    async def test_unsubscribe(self, client: AsyncClient):
        resp = await client.post("/api/v1/outreach/unsubscribe", params={"email": "test@example.com"})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "unsubscribed"

    async def test_suppression_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/outreach/compliance/suppression-list")
        assert resp.status_code == 200
        assert "suppressed" in resp.json()["data"]

    async def test_warmup_status(self, client: AsyncClient):
        resp = await client.get("/api/v1/outreach/compliance/warmup-status", params={"domain": "shipstudio.dev"})
        assert resp.status_code == 200
        assert resp.json()["data"]["daily_limit"] > 0


class TestSequences:
    """Sequence endpoint tests."""

    async def test_get_default_sequence(self, client: AsyncClient):
        resp = await client.get("/api/v1/outreach/sequences/default")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["steps"]) > 0
        assert data["data"]["steps"][0]["day"] == 0


class TestCampaignAndSend:
    """Campaign and sending tests."""

    async def test_create_campaign(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/outreach/campaigns",
            params={"name": "Q2 Campaign", "channels": ["email", "linkedin"]},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "Q2 Campaign"

    async def test_list_campaigns(self, client: AsyncClient):
        resp = await client.get("/api/v1/outreach/campaigns")
        assert resp.status_code == 200