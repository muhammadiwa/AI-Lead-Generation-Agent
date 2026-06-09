"""Follow-up sequence manager — schedules and manages multi-step outreach sequences."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SequenceStep:
    """A single step in an outreach sequence."""
    day: int                      # Day offset from start (0 = initial)
    channel: str                  # 'email' or 'linkedin'
    action: str                   # 'send_email', 'connection_request', 'send_message', 'share_post'
    subject_variants: List[str] = field(default_factory=list)
    body_template: str = ""
    wait_for_reply: bool = True
    stop_on_reply: bool = True
    condition: Optional[str] = None  # 'no_reply', 'connected_no_reply', etc.


DEFAULT_SEQUENCE = [
    SequenceStep(day=0, channel="email", action="send_email",
                 subject_variants=["{{company_name}}'s {{tech}} setup — quick thought",
                                   "Noticed {{company_name}} is hiring for {{role}}"],
                 body_template=""),
    SequenceStep(day=0, channel="linkedin", action="connection_request",
                 body_template="Hi {{first_name}}, I've been following {{company_name}}'s work in {{industry}}. Would love to connect.",
                 wait_for_reply=True),
    SequenceStep(day=3, channel="email", action="send_email",
                 condition="no_reply",
                 subject_variants=["Re: {{company_name}}'s {{tech}} — also noticed",
                                   "Following up + {{value_add_topic}}"],
                 body_template=""),
    SequenceStep(day=7, channel="email", action="send_email",
                 condition="no_reply",
                 subject_variants=["How we helped {{similar_company}} {{result}}",
                                   "{{company_name}} — relevant case study"],
                 body_template=""),
    SequenceStep(day=7, channel="linkedin", action="send_message",
                 condition="connected_no_reply",
                 body_template="Thanks for connecting, {{first_name}}! Noticed {{company_name}} {{specific_observation}}. If you're ever looking to scale your engineering, happy to share how we've helped similar teams.",
                 wait_for_reply=True),
    SequenceStep(day=14, channel="email", action="send_email",
                 condition="no_reply",
                 subject_variants=["Wrapping up — {{company_name}}",
                                   "Re: {{company_name}}"],
                 body_template=""),
    SequenceStep(day=30, channel="email", action="send_email",
                 condition="no_reply",
                 subject_variants=["{{company_name}} — circling back",
                                   "Checking in"],
                 body_template=""),
]


class FollowUpSequencer:
    """Manages follow-up sequences for outreach campaigns."""

    def __init__(self):
        self._sequences: Dict[str, List[SequenceStep]] = {}

    def register_sequence(self, name: str, steps: List[SequenceStep]):
        """Register a named sequence."""
        self._sequences[name] = steps

    def get_steps(self, sequence_name: str = "default") -> List[SequenceStep]:
        """Get the steps for a sequence."""
        if sequence_name in self._sequences:
            return self._sequences[sequence_name]
        return DEFAULT_SEQUENCE

    def get_due_steps(
        self,
        started_at: datetime,
        replied_at: Optional[datetime] = None,
        last_step_completed: int = 0,
        sequence_name: str = "default",
    ) -> List[SequenceStep]:
        """Get steps that are due to execute based on time elapsed."""
        if replied_at:
            return []  # Stop all sequences if replied

        steps = self.get_steps(sequence_name)
        now = datetime.now(timezone.utc)
        elapsed_days = (now - started_at).days
        due = []

        for step in steps[last_step_completed:]:
            if step.day <= elapsed_days:
                due.append(step)
            else:
                break

        return due

    def should_stop_sequence(self, replied: bool, sentiment: str) -> bool:
        """Determine if a sequence should be stopped based on reply."""
        if not replied:
            return False
        if sentiment in ("positive", "negative"):
            return True
        return False


# Singleton with default sequence
sequencer = FollowUpSequencer()
sequencer.register_sequence("default", DEFAULT_SEQUENCE)