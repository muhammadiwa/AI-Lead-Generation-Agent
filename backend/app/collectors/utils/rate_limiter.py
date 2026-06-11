"""Rate limiter for API and scrape operations."""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Dict, Optional


class TokenBucket:
    """Token bucket rate limiter per source."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate  # tokens per second
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> float:
        """Acquire tokens, returning wait time in seconds."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0

            deficit = tokens - self.tokens
            wait = deficit / self.rate
            self.tokens = 0.0
            return wait


class RateLimiter:
    """Multi-source rate limiter."""

    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._default_rate = 10.0  # 10 requests per second
        self._default_burst = 20

    def register_source(
        self, source: str, rate: Optional[float] = None, burst: Optional[int] = None
    ):
        self._buckets[source] = TokenBucket(
            rate=rate or self._default_rate,
            burst=burst or self._default_burst,
        )

    async def wait(self, source: str, tokens: int = 1):
        """Block until tokens are available for the given source."""
        if source not in self._buckets:
            self.register_source(source)
        wait_time = await self._buckets[source].acquire(tokens)
        if wait_time > 0:
            await asyncio.sleep(wait_time)


# Global rate limiter instance
rate_limiter = RateLimiter()