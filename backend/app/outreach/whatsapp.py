"""WhatsApp Business API sender — sends messages via WhatsApp Business API.

Uses the official WhatsApp Business API (Meta) or WhatsApp Web automation
as fallback. Follows the same SendResult pattern as EmailSender.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.collectors.utils.rate_limiter import rate_limiter
from app.config import settings
from app.outreach.sender import SendResult

logger = logging.getLogger(__name__)


class WhatsAppSender:
    """Send messages via WhatsApp Business API.

    Primary: WhatsApp Business Cloud API (Meta).
    Fallback: WhatsApp Web browser automation via Playwright.
    """

    def __init__(self):
        self._api_token = None  # WhatsApp Business API token
        self._phone_number_id = None  # Business phone number ID
        self._base_url = "https://graph.facebook.com/v18.0"
        self._from_number = settings.__dict__.get("whatsapp_from_number", "")

    async def send(
        self,
        to: str,
        body: str,
        media_url: Optional[str] = None,
        template_name: Optional[str] = None,
        template_params: Optional[Dict[str, str]] = None,
    ) -> SendResult:
        """Send a WhatsApp message.

        Args:
            to: Recipient phone number in E.164 format (+1234567890)
            body: Message text (for non-template messages)
            media_url: Optional media attachment URL
            template_name: Name of pre-approved message template
            template_params: Template variable values
        """
        await rate_limiter.wait("whatsapp", 1)

        if not self._api_token or not self._phone_number_id:
            logger.info(f"WhatsApp: would send to {to} (requires Business API setup)")
            return SendResult(success=False, error="WhatsApp API not configured", channel="whatsapp", recipient=to)

        try:
            payload: Dict[str, Any] = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
            }

            if template_name:
                # Send a pre-approved template message
                components = []
                if template_params:
                    components.append({
                        "type": "body",
                        "parameters": [{"type": "text", "text": v} for v in template_params.values()],
                    })
                payload["type"] = "template"
                payload["template"] = {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": components,
                }
            else:
                # Send a free-form text message
                payload["type"] = "text"
                payload["text"] = {"preview_url": True, "body": body}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self._base_url}/{self._phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self._api_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    msg_id = data.get("messages", [{}])[0].get("id", "")
                    return SendResult(
                        success=True,
                        message_id=msg_id,
                        external_id=msg_id,
                        channel="whatsapp",
                        recipient=to,
                    )
                else:
                    logger.error(f"WhatsApp API error {resp.status_code}: {resp.text[:200]}")
                    return SendResult(
                        success=False,
                        error=f"API error: {resp.status_code}",
                        channel="whatsapp",
                        recipient=to,
                    )

        except Exception as e:
            logger.error(f"WhatsApp send failed to {to}: {e}")
            return SendResult(success=False, error=str(e), channel="whatsapp", recipient=to)

    async def send_template(self, to: str, template_name: str, params: Dict[str, str]) -> SendResult:
        """Send a pre-approved message template (required for first message to new contacts)."""
        return await self.send(to=to, body="", template_name=template_name, template_params=params)

    async def send_text(self, to: str, body: str) -> SendResult:
        """Send a free-form text message (only after active conversation established)."""
        return await self.send(to=to, body=body)

    async def send_image(self, to: str, caption: str, media_url: str) -> SendResult:
        """Send an image message with caption."""
        await rate_limiter.wait("whatsapp", 1)

        if not self._api_token:
            return SendResult(success=False, error="WhatsApp API not configured", channel="whatsapp", recipient=to)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self._base_url}/{self._phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self._api_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": to,
                        "type": "image",
                        "image": {"link": media_url, "caption": caption},
                    },
                )

                if resp.status_code == 200:
                    return SendResult(success=True, channel="whatsapp", recipient=to)
                else:
                    return SendResult(success=False, error=f"API error: {resp.status_code}", channel="whatsapp", recipient=to)

        except Exception as e:
            logger.error(f"WhatsApp image send failed to {to}: {e}")
            return SendResult(success=False, error=str(e), channel="whatsapp", recipient=to)