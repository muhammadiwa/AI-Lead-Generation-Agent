"""Reply classifier — detects positive/negative/neutral sentiment from reply content."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class ReplySentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of classifying a reply."""
    sentiment: ReplySentiment
    confidence: float
    matched_keywords: List[str]
    suggested_action: str


# Keyword patterns for sentiment detection
POSITIVE_PATTERNS = [
    r"\b(interested?|let'?s\s+talk|schedule|tell\s+me\s+more)\b",
    r"\b(yes|sounds?\s+good|when\s+are\s+you\s+free)\b",
    r"\b(let'?s\s+discuss|open\s+to|would\s+love\s+to)\b",
    r"\b(great|awesome|perfect|excellent)\b",
    r"\b(how\s+much|pricing|cost|quote|proposal)\b",
    r"\b(book\s+a\s+call|set\s+up\s+a\s+time|calendar)\b",
]

NEGATIVE_PATTERNS = [
    r"\b(not\s+interested|unsubscri(be|bed)|remove\s+me)\b",
    r"\b(stop\s+emailing|don'?t\s+contact|leave\s+me\s+alone)\b",
    r"\b(not\s+right\s+now|not\s+at\s+this\s+time|no\s+thanks)\b",
    r"\b(spam|scam|waste\s+of\s+time|annoying)\b",
    r"\b(go\s+away|fuck\s+off|piss\s+off)\b",
]

NEUTRAL_PATTERNS = [
    r"\b(not\s+now|too\s+busy|maybe\s+later)\b",
    r"\b(send\s+me\s+(info|details|more))\b",
    r"\b(not\s+the\s+(right\s+)?person|forward(ing)?\s+to)\b",
    r"\b(can\s+you\s+send|tell\s+me\s+more|what\s+kind)\b",
    r"\b(out\s+of\s+office|OOO|vacation|holiday)\b",
]


class ReplyClassifier:
    """Classify reply sentiment using keyword patterns."""

    def __init__(self):
        self._positive = [re.compile(p, re.IGNORECASE) for p in POSITIVE_PATTERNS]
        self._negative = [re.compile(p, re.IGNORECASE) for p in NEGATIVE_PATTERNS]
        self._neutral = [re.compile(p, re.IGNORECASE) for p in NEUTRAL_PATTERNS]

    def classify(self, reply_text: str) -> ClassificationResult:
        """Classify a reply's sentiment and suggest the appropriate action."""
        if not reply_text or not reply_text.strip():
            return ClassificationResult(
                sentiment=ReplySentiment.UNKNOWN,
                confidence=0.0,
                matched_keywords=[],
                suggested_action="Investigate — empty reply",
            )

        matched_positive = self._match_patterns(self._positive, reply_text)
        matched_negative = self._match_patterns(self._negative, reply_text)
        matched_neutral = self._match_patterns(self._neutral, reply_text)

        # Score-based classification
        positive_score = len(matched_positive)
        negative_score = len(matched_negative)
        neutral_score = len(matched_neutral)

        if negative_score > positive_score and negative_score >= neutral_score:
            return ClassificationResult(
                sentiment=ReplySentiment.NEGATIVE,
                confidence=min(0.5 + negative_score * 0.15, 0.95),
                matched_keywords=matched_negative,
                suggested_action="Suppress immediately — move to lost, add to suppression list",
            )
        elif positive_score > 0 and positive_score >= neutral_score:
            return ClassificationResult(
                sentiment=ReplySentiment.POSITIVE,
                confidence=min(0.5 + positive_score * 0.15, 0.95),
                matched_keywords=matched_positive,
                suggested_action="Flag as hot lead — send calendar link, notify human",
            )
        elif neutral_score > 0:
            return ClassificationResult(
                sentiment=ReplySentiment.NEUTRAL,
                confidence=min(0.4 + neutral_score * 0.1, 0.8),
                matched_keywords=matched_neutral,
                suggested_action="Nurture — move to longer cadence, ask clarifying question",
            )
        else:
            return ClassificationResult(
                sentiment=ReplySentiment.UNKNOWN,
                confidence=0.3,
                matched_keywords=[],
                suggested_action="Manual review — no clear signal detected",
            )

    def _match_patterns(self, patterns: List[re.Pattern], text: str) -> List[str]:
        """Find all matching keywords in text for a set of patterns."""
        matches = []
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                matches.append(match.group(0))
        return matches

    def get_action_for_sentiment(self, sentiment: ReplySentiment) -> str:
        """Get the recommended business action for a sentiment."""
        actions = {
            ReplySentiment.POSITIVE: "Send calendar booking link, notify team via Slack",
            ReplySentiment.NEGATIVE: "Add to suppression list, stop all sequences, mark as lost",
            ReplySentiment.NEUTRAL: "Evaluate further, adjust cadence, consider manual follow-up",
            ReplySentiment.UNKNOWN: "Route for manual review before any automated action",
        }
        return actions.get(sentiment, "Unknown")


# Singleton
reply_classifier = ReplyClassifier()