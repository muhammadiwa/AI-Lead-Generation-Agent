"""Proxy rotation utilities for avoiding IP-based blocking."""
from __future__ import annotations

import random
from typing import Dict, List, Optional

from app.config import settings


class ProxyRotator:
    """Rotates through a list of proxies to distribute requests."""

    def __init__(self, proxies: Optional[List[str]] = None):
        self._proxies: List[str] = proxies or []
        self._index = 0

        # Parse from env if provided
        if not self._proxies and settings.proxy_list:
            self._proxies = [p.strip() for p in settings.proxy_list.split(",") if p.strip()]

        self._enabled = settings.proxy_rotation_enabled and len(self._proxies) > 0

    @property
    def has_proxies(self) -> bool:
        return self._enabled

    def next(self) -> Optional[Dict[str, str]]:
        """Get the next proxy in round-robin fashion."""
        if not self._enabled or not self._proxies:
            return None

        proxy_url = self._proxies[self._index % len(self._proxies)]
        self._index += 1

        return {
            "http": proxy_url,
            "https": proxy_url,
        }

    def random(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the pool."""
        if not self._enabled or not self._proxies:
            return None

        proxy_url = random.choice(self._proxies)
        return {
            "http": proxy_url,
            "https": proxy_url,
        }

    def add_proxy(self, proxy: str):
        """Add a proxy to the pool."""
        if proxy not in self._proxies:
            self._proxies.append(proxy)
            self._enabled = True


# Global proxy rotator
proxy_rotator = ProxyRotator()