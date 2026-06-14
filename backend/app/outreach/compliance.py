"""Compliance manager — unsubscribe handling, suppression lists, domain warmup, bounce management."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class SuppressionEntry:
    """A suppressed contact (unsubscribed, bounced, or complained)."""
    email: str
    reason: str  # 'unsubscribed', 'bounced', 'complaint', 'hard_bounce'
    timestamp: datetime
    source_campaign: Optional[str] = None


class ComplianceManager:
    """Manage email compliance — suppression list, unsubscribe, bounce handling."""

    def __init__(self):
        self._suppression_list: Dict[str, SuppressionEntry] = {}
        self._bounce_counts: Dict[str, int] = {}
        self._max_bounces = 3  # Auto-suppress after 3 bounces

    def unsubscribe(self, email: str, campaign: Optional[str] = None):
        """Add an email to the suppression list (unsubscribe)."""
        self._suppression_list[email] = SuppressionEntry(
            email=email,
            reason="unsubscribed",
            timestamp=datetime.now(timezone.utc),
            source_campaign=campaign,
        )
        logger.info(f"Unsubscribed: {email}")

    def record_bounce(self, email: str, bounce_type: str = "soft"):
        """Record a bounce and auto-suppress if threshold exceeded."""
        self._bounce_counts[email] = self._bounce_counts.get(email, 0) + 1

        if bounce_type == "hard" or self._bounce_counts[email] >= self._max_bounces:
            self._suppression_list[email] = SuppressionEntry(
                email=email,
                reason="hard_bounce" if bounce_type == "hard" else "bounced",
                timestamp=datetime.now(timezone.utc),
            )
            logger.info(f"Auto-suppressed {email} after {self._bounce_counts[email]} bounces")

    def is_suppressed(self, email: str) -> bool:
        """Check if an email is on the suppression list."""
        return email.lower() in {k.lower() for k in self._suppression_list}

    def get_suppression_list(self) -> List[Dict[str, str]]:
        """Get the full suppression list (for GDPR export)."""
        return [
            {
                "email": entry.email,
                "reason": entry.reason,
                "timestamp": entry.timestamp.isoformat(),
                "source": entry.source_campaign or "unknown",
            }
            for entry in self._suppression_list.values()
        ]

    def remove_from_suppression(self, email: str):
        """Remove an email from the suppression list."""
        key = next((k for k in self._suppression_list if k.lower() == email.lower()), None)
        if key:
            del self._suppression_list[key]
            logger.info(f"Removed from suppression: {email}")

    def generate_unsubscribe_link(self, email: str, campaign_id: str) -> str:
        """Generate an unsubscribe URL with HMAC token."""
        import hashlib
        token = hashlib.sha256(f"{email}:{campaign_id}:shipstudio-secret".encode()).hexdigest()[:16]
        return f"/api/v1/outreach/unsubscribe?email={email}&token={token}&campaign={campaign_id}"

    def validate_unsubscribe_token(self, email: str, token: str, campaign_id: str) -> bool:
        """Validate an unsubscribe token."""
        import hashlib
        expected = hashlib.sha256(f"{email}:{campaign_id}:shipstudio-secret".encode()).hexdigest()[:16]
        return token == expected


class WarmupManager:
    """Manage email domain warm-up schedules and daily send limits."""

    def __init__(self):
        self._domains: Dict[str, "WarmupConfig"] = {}

    def register_domain(self, domain: str, start_date: Optional[date] = None):
        """Register a sending domain for warm-up tracking."""
        self._domains[domain] = WarmupConfig(
            domain=domain,
            start_date=start_date or date.today(),
        )

    def get_daily_limit(self, domain: str) -> int:
        """Get the maximum emails to send today for a domain based on warm-up stage."""
        config = self._domains.get(domain)
        if not config:
            return 5  # Conservative default for unregistered domains

        days_active = (date.today() - config.start_date).days

        if days_active < 3:
            return 5
        elif days_active < 7:
            return 10
        elif days_active < 14:
            return 20
        elif days_active < 21:
            return 30
        elif days_active < 28:
            return 40
        else:
            return 50

    def is_fully_warmed(self, domain: str) -> bool:
        """Check if a domain has completed warm-up."""
        config = self._domains.get(domain)
        if not config:
            return False
        return (date.today() - config.start_date).days >= 28


@dataclass
class WarmupConfig:
    domain: str
    start_date: date
    current_limit: int = 5


# Singletons
compliance = ComplianceManager()
warmup = WarmupManager()