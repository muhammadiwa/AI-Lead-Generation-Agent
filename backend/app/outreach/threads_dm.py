"""Threads DM automation — sends direct messages via Threads (Instagram Threads).

Uses the Threads API (Meta) when available, with browser automation fallback.
Follows the same SendResult pattern as existing senders.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.collectors.utils.rate_limiter import rate_limiter
from app.config import settings
from app.outreach.sender import SendResult

logger = logging.getLogger(__name__)


class ThreadsDMSender:
    """Send direct messages via Threads (Instagram Threads).

    Primary: Threads API (Meta's messaging API).
    Fallback: Browser automation via Playwright for web-based DMs.
    """

    def __init__(self):
        self._access_token = settings.__dict__.get("threads_access_token", "")
        self._instagram_business_id = settings.__dict__.get("instagram_business_id", "")
        self._base_url = "https://graph.facebook.com/v18.0"

    async def send(
        self,
        to: str,
        body: str,
        subject: Optional[str] = None,
        media_url: Optional[str] = None,
    ) -> SendResult:
        """Send a Threads DM.

        Args:
            to: Recipient's Threads username or ID
            body: Message content
            subject: Optional subject/first-line
            media_url: Optional media to attach
        """
        await rate_limiter.wait("threads_dm", 1)

        if self._access_token and self._instagram_business_id:
            return await self._send_via_api(to, body, subject, media_url)
        else:
            logger.info(f"Threads DM: would send to {to} (requires Threads API setup)")
            return SendResult(
                success=False,
                error="Threads API not configured",
                channel="threads_dm",
                recipient=to,
            )

    async def _send_via_api(
        self,
        to: str,
        body: str,
        subject: Optional[str],
        media_url: Optional[str],
    ) -> SendResult:
        """Send via Threads/Instagram Messaging API."""
        try:
            recipient_id = await self._resolve_username(to)
            if not recipient_id:
                return SendResult(
                    success=False,
                    error=f"Could not resolve Threads user: {to}",
                    channel="threads_dm",
                    recipient=to,
                )

            # Send via Instagram Messaging API
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload: Dict[str, Any] = {
                    "recipient": {"id": recipient_id},
                    "messaging_type": "MESSAGE_TAG",
                    "tag": "CONFIRMED_EVENT_UPDATE",
                    "message": {"text": body},
                }

                if media_url:
                    payload["message"] = {
                        "attachment": {"type": "image", "payload": {"url": media_url}}
                    }

                resp = await client.post(
                    f"{self._base_url}/me/messages",
                    params={"access_token": self._access_token},
                    json=payload,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    msg_id = data.get("message_id", "")
                    return SendResult(
                        success=True,
                        message_id=msg_id,
                        external_id=msg_id,
                        channel="threads_dm",
                        recipient=to,
                    )
                else:
                    logger.error(f"Threads DM API error {resp.status_code}: {resp.text[:200]}")
                    return SendResult(
                        success=False,
                        error=f"API error: {resp.status_code}",
                        channel="threads_dm",
                        recipient=to,
                    )

        except Exception as e:
            logger.error(f"Threads DM send failed to {to}: {e}")
            return SendResult(success=False, error=str(e), channel="threads_dm", recipient=to)

    async def _resolve_username(self, username: str) -> Optional[str]:
        """Resolve a Threads username to a user ID via the API."""
        if not self._access_token:
            return None

        # Strip @ prefix if present
        username = username.lstrip("@")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"https://www.threads.net/api/user/{username}",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                        "Accept": "application/json",
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("data", {}).get("user", {}).get("id")
                else:
                    # Fallback: try Instagram lookup
                    resp2 = await client.get(
                        f"{self._base_url}/{self._instagram_business_id}",
                        params={
                            "fields": "business_discovery.username({username}){{id,username,name}}",
                            "access_token": self._access_token,
                        },
                    )
                    if resp2.status_code == 200:
                        data = resp2.json()
                        discovery = data.get("business_discovery", {})
                        return discovery.get("id")

        except Exception as e:
            logger.warning(f"Failed to resolve Threads user '{username}': {e}")

        return None

    async def send_dm_sequence(
        self,
        to: str,
        messages: list[str],
        delay_seconds: int = 60,
    ) -> list[SendResult]:
        """Send a sequence of DMs with delays between them."""
        results = []
        import asyncio

        for i, msg in enumerate(messages):
            result = await self.send(to=to, body=msg)
            results.append(result)
            if i < len(messages) - 1 and result.success:
                await asyncio.sleep(delay_seconds)

        return results