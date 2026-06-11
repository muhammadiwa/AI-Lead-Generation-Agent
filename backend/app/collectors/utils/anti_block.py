"""Anti-blocking strategies: headers, fingerprints, delays, retries."""
from __future__ import annotations

import random
import time
from typing import Dict, Optional


# Common user-agent strings to rotate through
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


def random_user_agent() -> str:
    """Return a random user-agent string."""
    return random.choice(USER_AGENTS)


def random_delay(min_sec: float = 1.0, max_sec: float = 5.0) -> float:
    """Sleep for a random duration between min_sec and max_sec seconds."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


async def async_random_delay(min_sec: float = 1.0, max_sec: float = 5.0) -> float:
    """Async sleep for a random duration."""
    import asyncio

    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)
    return delay


def build_headers(referer: Optional[str] = None, accept_language: str = "en-US,en;q=0.9") -> Dict[str, str]:
    """Build realistic browser-like headers."""
    headers = {
        "User-Agent": random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": accept_language,
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def build_json_api_headers(api_key: Optional[str] = None) -> Dict[str, str]:
    """Build headers for JSON API calls."""
    headers = {
        "User-Agent": random_user_agent(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers