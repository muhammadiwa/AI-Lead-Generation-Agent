"""Outreach tracker — open/click/reply tracking via webhooks and pixel tracking."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TrackingEvent:
    """A single tracking event for a message."""
    event_type: str  # 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'unsubscribed'
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class OutreachTracker:
    """Tracks message engagement — opens, clicks, replies, bounces."""

    def __init__(self):
        self._events: Dict[str, List[TrackingEvent]] = {}

    def record_event(
        self,
        message_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a tracking event for a message."""
        if message_id not in self._events:
            self._events[message_id] = []
        self._events[message_id].append(TrackingEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        ))
        logger.info(f"Tracking: message {message_id} -> {event_type}")

    def get_events(self, message_id: str) -> List[Dict[str, Any]]:
        """Get all tracking events for a message."""
        events = self._events.get(message_id, [])
        return [
            {
                "event": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "metadata": e.metadata,
            }
            for e in events
        ]

    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get the current engagement status of a message."""
        events = self._events.get(message_id, [])
        status = "unknown"

        event_types = [e.event_type for e in events]
        if "bounced" in event_types:
            status = "bounced"
        elif "replied" in event_types:
            status = "replied"
        elif "clicked" in event_types:
            status = "clicked"
        elif "opened" in event_types:
            status = "opened"
        elif "delivered" in event_types:
            status = "delivered"
        elif "sent" in event_types:
            status = "sent"

        return {
            "message_id": message_id,
            "status": status,
            "events": len(events),
            "last_event": events[-1].event_type if events else None,
            "last_timestamp": events[-1].timestamp.isoformat() if events else None,
        }

    def get_campaign_summary(self, message_ids: List[str]) -> Dict[str, Any]:
        """Get summary stats for a set of messages."""
        total = len(message_ids)
        delivered = 0
        opened = 0
        clicked = 0
        replied = 0
        bounced = 0

        for mid in message_ids:
            events = self._events.get(mid, [])
            types = [e.event_type for e in events]
            if "bounced" in types:
                bounced += 1
            elif "replied" in types:
                replied += 1
            elif "clicked" in types:
                clicked += 1
            elif "opened" in types:
                opened += 1
            elif "delivered" in types:
                delivered += 1

        return {
            "total_sent": total,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "bounced": bounced,
            "open_rate": round((opened / total * 100), 2) if total > 0 else 0,
            "reply_rate": round((replied / total * 100), 2) if total > 0 else 0,
            "bounce_rate": round((bounced / total * 100), 2) if total > 0 else 0,
        }

    def generate_tracking_pixel(self, message_id: str) -> str:
        """Generate a tracking pixel URL for open detection."""
        # In production, this would be a 1x1 transparent GIF endpoint
        return f"/api/v1/track/open/{message_id}"


# Singleton
tracker = OutreachTracker()