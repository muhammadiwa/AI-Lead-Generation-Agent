"""Tests for WhatsApp and Threads DM automation."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestWhatsAppAPI:
    """WhatsApp API integration tests."""

    async def test_whatsapp_status(self, client: AsyncClient):
        resp = await client.get("/api/v1/outreach/whatsapp/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "configured" in data["data"]

    async def test_whatsapp_send_no_config(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/outreach/whatsapp/send",
            params={"to": "+1234567890", "body": "Hello from Ship Studio!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["success"] is False
        assert "not configured" in data["data"]["error"].lower()


class TestThreadsDMAPI:
    """Threads DM API integration tests."""

    async def test_threads_status(self, client: AsyncClient):
        resp = await client.get("/api/v1/outreach/threads/status")
        assert resp.status_code == 200
        assert "configured" in resp.json()["data"]

    async def test_threads_send_no_config(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/outreach/threads/send",
            params={"to": "@startup_founder", "body": "Love your work!"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["success"] is False
        assert "not configured" in resp.json()["data"]["error"]

    async def test_threads_sequence_no_config(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/outreach/threads/sequence",
            json={"to": "@founder", "messages": ["Hi!", "Following up..."], "delay_seconds": 30},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["results"]) == 2
        for r in data["data"]["results"]:
            assert r["success"] is False