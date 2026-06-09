"""Webhook system — outgoing webhooks for external integrations (Slack, HubSpot, CRM)."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.schemas import APIResponse
from app.core import success_response
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])


@dataclass
class WebhookRegistration:
    """A registered outgoing webhook endpoint."""
    id: str
    url: str
    events: List[str]          # e.g. ['lead.discovered', 'lead.qualified', 'outreach.sent']
    secret: str                # HMAC signing secret
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    last_sent_at: Optional[float] = None
    failure_count: int = 0


class WebhookManager:
    """Manages outgoing webhooks — register, fire, retry, HMAC sign."""

    def __init__(self):
        self._webhooks: Dict[str, WebhookRegistration] = {}
        self.MAX_RETRIES = 3
        self.RETRY_DELAYS = [5, 30, 120]  # seconds between retries

    def register(self, url: str, events: List[str], secret: Optional[str] = None) -> str:
        """Register a new webhook endpoint."""
        webhook_id = str(uuid.uuid4())
        self._webhooks[webhook_id] = WebhookRegistration(
            id=webhook_id,
            url=url,
            events=events,
            secret=secret or hashlib.sha256(f"{url}:{webhook_id}".encode()).hexdigest()[:32],
        )
        logger.info(f"Registered webhook {webhook_id} for events: {events}")
        return webhook_id

    def unregister(self, webhook_id: str) -> bool:
        """Remove a webhook registration."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False

    def get_registrations(self) -> List[Dict[str, Any]]:
        """List all registered webhooks."""
        return [
            {
                "id": w.id,
                "url": w.url,
                "events": w.events,
                "is_active": w.is_active,
                "failure_count": w.failure_count,
            }
            for w in self._webhooks.values()
        ]

    async def fire_event(self, event: str, data: Dict[str, Any]):
        """Fire an event to all matching webhooks."""
        for webhook in self._webhooks.values():
            if not webhook.is_active:
                continue
            if event not in webhook.events:
                continue

            payload = {
                "event": event,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }

            await self._send_with_retry(webhook, payload)

    async def _send_with_retry(self, webhook: WebhookRegistration, payload: Dict[str, Any]):
        """Send webhook payload with HMAC signing and retry logic."""
        payload_bytes = json.dumps(payload).encode()
        signature = hmac.new(
            webhook.secret.encode(),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": payload.get("event", "unknown"),
            "X-Webhook-ID": webhook.id,
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                    )

                    if resp.status_code < 300:
                        webhook.last_sent_at = time.time()
                        logger.info(f"Webhook {webhook.id} -> {webhook.url}: {resp.status_code}")
                        return
                    else:
                        logger.warning(f"Webhook {webhook.id} returned {resp.status_code}: {resp.text[:200]}")

            except Exception as e:
                logger.warning(f"Webhook {webhook.id} attempt {attempt + 1} failed: {e}")

            if attempt < self.MAX_RETRIES - 1:
                delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                import asyncio
                await asyncio.sleep(delay)

        webhook.failure_count += 1
        logger.error(f"Webhook {webhook.id} failed after {self.MAX_RETRIES} attempts")


# Singleton
webhook_manager = WebhookManager()


# ─── API Endpoints ───

@router.post("/webhooks/register", response_model=APIResponse, status_code=201)
async def register_webhook(url: str, events: list[str], secret: Optional[str] = None):
    """Register an outgoing webhook."""
    wh_id = webhook_manager.register(url, events, secret)
    return success_response(data={"id": wh_id, "url": url, "events": events})


@router.get("/webhooks/registrations", response_model=APIResponse)
async def list_webhooks():
    """List all registered webhooks."""
    return success_response(data={"webhooks": webhook_manager.get_registrations()})


@router.delete("/webhooks/registrations/{webhook_id}", response_model=APIResponse)
async def delete_webhook(webhook_id: str):
    """Delete a webhook registration."""
    if webhook_manager.unregister(webhook_id):
        return success_response(data={"id": webhook_id, "deleted": True})
    from app.core.errors import NotFoundError
    raise NotFoundError("Webhook", webhook_id)


@router.post("/webhooks/test-fire", response_model=APIResponse)
async def test_fire_webhook(
    webhook_id: str,
    event: str = "test.event",
    data: Dict[str, Any] = {"message": "Test event"},
):
    """Manually fire a test event to a webhook."""
    from app.core.errors import NotFoundError
    wh = next((w for w in webhook_manager.get_registrations() if w["id"] == webhook_id), None)
    if not wh:
        raise NotFoundError("Webhook", webhook_id)

    await webhook_manager.fire_event(event, data)
    return success_response(data={"fired": True, "webhook_id": webhook_id, "event": event})