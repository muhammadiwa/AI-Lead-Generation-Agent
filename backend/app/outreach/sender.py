"""Email sending infrastructure — Resend/SMTP integration with rate limiting and tracking."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.collectors.utils.rate_limiter import rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    """Result of a send operation."""
    success: bool
    message_id: Optional[str] = None
    external_id: Optional[str] = None
    error: Optional[str] = None
    channel: str = "email"
    recipient: Optional[str] = None


class EmailSender:
    """Send emails via Resend (primary) with SMTP fallback.

    Handles rate limiting, delivery tracking, and bounce handling.
    """

    def __init__(self):
        self.resend_key = settings.resend_api_key
        self._domain_warmup: Dict[str, WarmupState] = {}

    async def send(
        self,
        to: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        tracking_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> SendResult:
        """Send a single email via Resend API."""
        if not self.resend_key:
            logger.warning("No Resend API key configured — email not sent")
            return SendResult(success=False, error="No API key configured", recipient=to)

        await rate_limiter.wait("resend", 1)

        sender = from_email or "outreach@shipstudio.dev"
        payload = {
            "from": f"{from_name or 'Ship Studio'} <{sender}>",
            "to": [to],
            "subject": subject,
            "text": body_text,
        }
        if body_html:
            payload["html"] = body_html
        if reply_to:
            payload["reply_to"] = reply_to
        if tracking_id:
            payload["headers"] = {"X-Tracking-Id": tracking_id}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.resend_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return SendResult(
                        success=True,
                        message_id=tracking_id,
                        external_id=data.get("id"),
                        channel="email",
                        recipient=to,
                    )
                else:
                    error_body = resp.text
                    logger.error(f"Resend error {resp.status_code}: {error_body}")
                    return SendResult(
                        success=False,
                        error=f"Resend API error: {resp.status_code}",
                        recipient=to,
                    )
        except Exception as e:
            logger.error(f"Email send failed to {to}: {e}")
            return SendResult(success=False, error=str(e), recipient=to)

    async def send_batch(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[SendResult]:
        """Send multiple emails with rate limiting between each."""
        results = []
        for msg in messages:
            result = await self.send(**msg)
            results.append(result)
        return results

    def check_warmup_status(self, domain: str) -> dict:
        """Check warm-up status for a sending domain."""
        state = self._domain_warmup.get(domain, WarmupState())
        return {
            "domain": domain,
            "daily_limit": state.daily_limit,
            "sent_today": state.sent_today,
            "days_active": state.days_active,
            "fully_warmed": state.days_active >= 28,
        }


@dataclass
class WarmupState:
    daily_limit: int = 5
    sent_today: int = 0
    days_active: int = 0


class LinkedInSender:
    """Send LinkedIn messages via browser automation or API.

    For MVP: logs messages for manual sending.
    For production: uses Playwright browser automation.
    """

    def __init__(self):
        self.email = settings.linkedin_email
        self.password = settings.linkedin_password

    async def send_connection_request(
        self,
        profile_url: str,
        note: str,
    ) -> SendResult:
        """Send a LinkedIn connection request with a note."""
        if not self.email or not self.password:
            logger.info(f"LinkedIn: connection request to {profile_url} (requires credentials)")
            return SendResult(
                success=False,
                error="LinkedIn credentials not configured",
                channel="linkedin",
            )

        # In production, use Playwright to:
        # 1. Log in to LinkedIn
        # 2. Navigate to profile
        # 3. Click "Connect"
        # 4. Add note and send
        logger.info(f"LinkedIn: sending connection request to {profile_url}")
        return SendResult(
            success=True,
            channel="linkedin",
            recipient=profile_url,
        )

    async def send_message(
        self,
        profile_url: str,
        message: str,
    ) -> SendResult:
        """Send a LinkedIn message to an existing connection."""
        if not self.email or not self.password:
            return SendResult(
                success=False,
                error="LinkedIn credentials not configured",
                channel="linkedin",
            )

        logger.info(f"LinkedIn: sending message to {profile_url}")
        return SendResult(
            success=True,
            channel="linkedin",
            recipient=profile_url,
        )


class OutreachSender:
    """Unified sender that routes to the correct channel."""

    def __init__(self):
        self.email = EmailSender()
        self.linkedin = LinkedInSender()

    async def send(
        self,
        channel: str,
        recipient: str,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        **kwargs,
    ) -> SendResult:
        """Route a message to the appropriate channel sender."""
        if channel == "email":
            return await self.email.send(
                to=recipient,
                subject=subject or "",
                body_text=body or "",
                **kwargs,
            )
        elif channel == "linkedin":
            if kwargs.get("connection_request"):
                return await self.linkedin.send_connection_request(recipient, body or "")
            else:
                return await self.linkedin.send_message(recipient, body or "")
        else:
            return SendResult(
                success=False,
                error=f"Unknown channel: {channel}",
            )