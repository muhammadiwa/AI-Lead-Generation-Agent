"""A/B testing framework — variant management and performance tracking."""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ABVariant:
    """A single variant in an A/B test."""
    name: str
    subject: Optional[str] = None
    body: Optional[str] = None
    channel: str = "email"


@dataclass
class ABTestResult:
    """Results accumulator for an A/B test."""
    variant_name: str
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    bounced: int = 0

    @property
    def open_rate(self) -> float:
        return (self.opened / self.delivered * 100) if self.delivered > 0 else 0.0

    @property
    def reply_rate(self) -> float:
        return (self.replied / self.delivered * 100) if self.delivered > 0 else 0.0

    @property
    def click_rate(self) -> float:
        return (self.clicked / self.delivered * 100) if self.delivered > 0 else 0.0

    def merge(self, other: "ABTestResult") -> "ABTestResult":
        return ABTestResult(
            variant_name=self.variant_name,
            sent=self.sent + other.sent,
            delivered=self.delivered + other.delivered,
            opened=self.opened + other.opened,
            clicked=self.clicked + other.clicked,
            replied=self.replied + other.replied,
            bounced=self.bounced + other.bounced,
        )


class ABTestingEngine:
    """Manages A/B testing of message variants with statistical tracking."""

    MIN_SAMPLE_PER_VARIANT = 50

    def __init__(self):
        self._results: Dict[str, List[ABTestResult]] = {}
        self._traffic_split: Dict[str, float] = {}

    def register_test(self, test_name: str, variants: List[ABVariant], control_pct: float = 80):
        """Register a new A/B test with variants."""
        if len(variants) < 2:
            raise ValueError("Need at least 2 variants for A/B testing")

        self._results[test_name] = [
            ABTestResult(variant_name=v.name) for v in variants
        ]
        challenger_pct = (100 - control_pct) / (len(variants) - 1) if len(variants) > 1 else 0
        self._traffic_split[test_name] = control_pct

        logger.info(f"Registered A/B test '{test_name}' with {len(variants)} variants, "
                    f"{control_pct}% to control")

    def select_variant(self, test_name: str, variants: List[ABVariant]) -> ABVariant:
        """Select a variant for a new message based on traffic split."""
        if not variants:
            raise ValueError("No variants provided")

        if len(variants) == 1:
            return variants[0]

        # Current winning variant gets more traffic
        results = self._get_results(test_name, variants)
        if results and all(r.sent >= self.MIN_SAMPLE_PER_VARIANT for r in results):
            # Use weighted selection based on reply rate
            total_replies = sum(r.replied for r in results)
            if total_replies > 0:
                weights = [r.reply_rate if r.reply_rate > 0 else 0.1 for r in results]
                total_weight = sum(weights)
                weights = [w / total_weight for w in weights]
                return random.choices(variants, weights=weights, k=1)[0]

        # Default: random selection with control bias
        if random.random() < 0.8:  # 80% to control (first variant)
            return variants[0]
        return random.choice(variants[1:])

    def record_result(self, test_name: str, variant_name: str, event: str):
        """Record an event for a variant (sent, opened, clicked, replied, bounced)."""
        for result in self._results.get(test_name, []):
            if result.variant_name == variant_name:
                if event == "sent":
                    result.sent += 1
                elif event == "delivered":
                    result.delivered += 1
                elif event == "opened":
                    result.opened += 1
                elif event == "clicked":
                    result.clicked += 1
                elif event == "replied":
                    result.replied += 1
                elif event == "bounced":
                    result.bounced += 1
                break

    def get_results(self, test_name: str) -> List[Dict[str, Any]]:
        """Get formatted results for a test."""
        results = self._results.get(test_name, [])
        return [
            {
                "variant": r.variant_name,
                "sent": r.sent,
                "delivered": r.delivered,
                "opened": r.opened,
                "open_rate": round(r.open_rate, 2),
                "clicked": r.clicked,
                "click_rate": round(r.click_rate, 2),
                "replied": r.replied,
                "reply_rate": round(r.reply_rate, 2),
                "bounced": r.bounced,
            }
            for r in results
        ]

    def get_winner(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Get the winning variant if statistically significant."""
        results = self._get_results(test_name)
        if not results or len(results) < 2:
            return None

        # Check minimum sample size
        if any(r.sent < self.MIN_SAMPLE_PER_VARIANT for r in results):
            return None

        # Winner = highest reply rate
        best = max(results, key=lambda r: r.reply_rate)
        return {
            "variant": best.variant_name,
            "reply_rate": round(best.reply_rate, 2),
            "open_rate": round(best.open_rate, 2),
            "samples": best.sent,
        }

    def _get_results(self, test_name: str, variants: Optional[List[ABVariant]] = None) -> List[ABTestResult]:
        """Get or create result trackers for variants."""
        if test_name not in self._results and variants:
            self._results[test_name] = [ABTestResult(variant_name=v.name) for v in variants]
        return self._results.get(test_name, [])


# Singleton
ab_testing = ABTestingEngine()