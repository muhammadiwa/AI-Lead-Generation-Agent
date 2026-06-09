"""NLP-based signal detection — classifies scraped content for lead intent signals."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LeadSignal:
    """A detected signal extracted from lead content."""
    signal_type: str  # e.g. 'hiring_developers', 'tech_debt', 'seeking_cto', 'funding_raised'
    strength: float   # 0.0 to 1.0
    source: str       # e.g. 'description', 'tech_stack', 'job_post', 'social'
    evidence: str     # The text evidence that triggered this signal
    category: str     # 'positive', 'negative', 'neutral'


# ─── Signal patterns — keyword/regex based detection ───

SIGNAL_PATTERNS: Dict[str, List[Dict[str, Any]]] = {
    "hiring_developers": [
        {"patterns": [r"hiring\s+(software\s+)?(engineer|developer|architect|cto)"], "weight": 0.7, "category": "positive"},
        {"patterns": [r"(looking|searching)\s+for\s+(a\s+)?(developer|engineer|cto|tech\s+lead)"], "weight": 0.6, "category": "positive"},
        {"patterns": [r"we\s+are\s+(hiring|recruiting|looking\s+for)"], "weight": 0.4, "category": "positive"},
        {"patterns": [r"job\s+(opening|posting|vacancy)"], "weight": 0.5, "category": "positive"},
        {"patterns": [r"(join\s+our\s+team|career|we\'?re\s+hiring)"], "weight": 0.5, "category": "positive"},
    ],
    "tech_debt": [
        {"patterns": [r"(outdated|legacy|old)\s+(tech|stack|system|infrastructure|codebase)"], "weight": 0.7, "category": "positive"},
        {"patterns": [r"(migrate|migration|rewrite|refactor|modernize)"], "weight": 0.6, "category": "positive"},
        {"patterns": [r"(monolith|technical\s+debt|spaghetti\s+code)"], "weight": 0.8, "category": "positive"},
        {"patterns": [r"(upgrade|upgrading)\s+(from|to)\s+\w+"], "weight": 0.5, "category": "positive"},
    ],
    "seeking_cto": [
        {"patterns": [r"(need|looking\s+for|hiring)\s+(a\s+)?(cto|vp\s+engineering)"], "weight": 0.8, "category": "positive"},
        {"patterns": [r"(co-founder|founding\s+engineer|founding\s+developer)"], "weight": 0.7, "category": "positive"},
        {"patterns": [r"(technical\s+co-founder|cto\s+position)"], "weight": 0.9, "category": "positive"},
    ],
    "recent_funding": [
        {"patterns": [r"(raised\s+\$[\d,]+[MBK]|secured\s+\$[\d,]+[MBK]|funding\s+of\s+\$[\d,]+)"], "weight": 0.8, "category": "positive"},
        {"patterns": [r"(series\s+[aAbBcC]\s+(round|funding)|seed\s+(round|funding))"], "weight": 0.7, "category": "positive"},
        {"patterns": [r"(investors?|venture\s+captial|vc\s+backed)"], "weight": 0.5, "category": "positive"},
    ],
    "rapid_growth": [
        {"patterns": [r"(growing|expanding|scaling)\s+(rapidly|quickly|fast)"], "weight": 0.6, "category": "positive"},
        {"patterns": [r"(\d+[%])\s+(growth|increase|yoy)"], "weight": 0.7, "category": "positive"},
        {"patterns": [r"(opening|expanding)\s+(new\s+)?offices?"], "weight": 0.5, "category": "positive"},
    ],
    "tech_stack_signal": [
        {"patterns": [r"(react|vue|angular|node\.?js|python|ruby|php|java|\.net)"], "weight": 0.3, "category": "neutral"},
        {"patterns": [r"(kubernetes|docker|aws|gcp|azure|terraform)"], "weight": 0.4, "category": "neutral"},
        {"patterns": [r"(wordpress|shopify|magento|drupal|joomla)"], "weight": 0.2, "category": "neutral"},
        {"patterns": [r"(tailwind|next\.?js|nuxt|svelte|solid)"], "weight": 0.3, "category": "neutral"},
        {"patterns": [r"(postgresql|mysql|mongodb|redis|elasticsearch)"], "weight": 0.3, "category": "neutral"},
    ],
    "pain_point": [
        {"patterns": [r"(challenge|problem|issue|struggl|difficult)\s+(with|in|of)"], "weight": 0.5, "category": "positive"},
        {"patterns": [r"(slow|expensive|costly|inefficient|manual)\s+(process|workflow|system)"], "weight": 0.6, "category": "positive"},
        {"patterns": [r"(need\s+(a\s+)?(better|new|modern|faster|scalable))"], "weight": 0.5, "category": "positive"},
    ],
    "decision_maker_present": [
        {"patterns": [r"(ceo|cto|founder|co-founder|owner|director)"], "weight": 0.4, "category": "neutral"},
        {"patterns": [r"(vp\s+(engineering|technology|product)|head\s+of\s+(engineering|tech|product))"], "weight": 0.6, "category": "neutral"},
    ],
}


class SignalDetector:
    """Detect intent signals from lead content using NLP patterns."""

    def __init__(self):
        self._compiled: Dict[str, List[Dict[str, Any]]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for signal_type, rules in SIGNAL_PATTERNS.items():
            compiled_rules = []
            for rule in rules:
                compiled = {
                    "compiled": [re.compile(p, re.IGNORECASE) for p in rule["patterns"]],
                    "weight": rule["weight"],
                    "category": rule["category"],
                }
                compiled_rules.append(compiled)
            self._compiled[signal_type] = compiled_rules

    def analyze(self, lead_data: Dict[str, Any]) -> List[LeadSignal]:
        """Analyze lead data and return detected signals."""
        signals: List[LeadSignal] = []
        text_content = self._extract_text(lead_data)

        for signal_type, rules in self._compiled.items():
            for rule in rules:
                for pattern in rule["compiled"]:
                    match = pattern.search(text_content)
                    if match:
                        signals.append(LeadSignal(
                            signal_type=signal_type,
                            strength=rule["weight"],
                            source="content_analysis",
                            evidence=match.group(0)[:200],
                            category=rule["category"],
                        ))
                        break  # One match per rule is enough

        # Detect signals from structured fields
        if lead_data.get("company_github_url"):
            signals.append(LeadSignal(
                signal_type="tech_stack_signal",
                strength=0.5,
                source="github",
                evidence="Company has GitHub presence",
                category="neutral",
            ))

        if lead_data.get("funding_total") and lead_data["funding_total"] > 0:
            signals.append(LeadSignal(
                signal_type="recent_funding",
                strength=0.6,
                source="funding_data",
                evidence=f"Funding total: ${lead_data['funding_total']}",
                category="positive",
            ))

        # Deduplicate signals — keep strongest per type
        return self._deduplicate(signals)

    def _extract_text(self, lead_data: Dict[str, Any]) -> str:
        """Extract all text content from a lead's data for analysis."""
        parts = []

        if lead_data.get("description"):
            parts.append(lead_data["description"])
        if lead_data.get("company_name"):
            parts.append(lead_data["company_name"])
        if lead_data.get("industry"):
            parts.append(lead_data["industry"])
        if lead_data.get("notes"):
            parts.append(lead_data["notes"])
        if lead_data.get("tags"):
            parts.append(" ".join(lead_data["tags"]))
        if lead_data.get("tech_stack"):
            stack = lead_data["tech_stack"]
            if isinstance(stack, dict):
                parts.append(str(stack.get("detected_technologies", [])))
                parts.append(str(stack.get("categories", {})))
        if lead_data.get("social_links"):
            parts.append(str(lead_data["social_links"]))
        if lead_data.get("funding_rounds"):
            for round_data in (lead_data["funding_rounds"] or []):
                if isinstance(round_data, dict):
                    parts.append(str(round_data.get("type", "")))
        if lead_data.get("employee_count"):
            parts.append(f"employee count {lead_data['employee_count']}")

        return " ".join(p for p in parts if p)

    def _deduplicate(self, signals: List[LeadSignal]) -> List[LeadSignal]:
        """Keep only the strongest signal per type."""
        best: Dict[str, LeadSignal] = {}
        for s in signals:
            if s.signal_type not in best or s.strength > best[s.signal_type].strength:
                best[s.signal_type] = s
        return list(best.values())


# Singleton
signal_detector = SignalDetector()