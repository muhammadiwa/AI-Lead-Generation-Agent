"""Vector embedding service — generates embeddings for lead similarity/search.

Supports OpenAI embeddings API and a lightweight local fallback using
character n-grams (no external dependencies required).
For production, use Qdrant or pgvector for vector storage and search.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LeadEmbedding:
    """A lead's vector embedding for similarity search."""
    lead_id: str
    vector: List[float]
    model: str
    dimension: int


class EmbeddingService:
    """Generate vector embeddings for lead similarity and search.

    Uses OpenAI embeddings API when configured, with a statistical
    fallback using character n-gram hashing for offline operation.
    """

    def __init__(self):
        self.openai_key = settings.openai_api_key
        self._dimension = 1536  # OpenAI ada-002 default

    async def embed(self, lead_data: Dict[str, Any]) -> Optional[LeadEmbedding]:
        """Generate embedding for a lead's text data."""
        text = self._build_embedding_text(lead_data)
        if not text:
            return None

        if self.openai_key:
            return await self._embed_openai(lead_data.get("id", ""), text)
        else:
            return self._embed_local(lead_data.get("id", ""), text)

    async def embed_batch(self, leads: List[Dict[str, Any]]) -> List[LeadEmbedding]:
        """Generate embeddings for multiple leads."""
        results = []
        for lead in leads:
            embedding = await self.embed(lead)
            if embedding:
                results.append(embedding)
        return results

    def _build_embedding_text(self, lead_data: Dict[str, Any]) -> str:
        """Build a text representation of a lead for embedding."""
        parts = [
            lead_data.get("company_name", ""),
            lead_data.get("description", ""),
            lead_data.get("industry", ""),
            " ".join(lead_data.get("tags") or []),
            lead_data.get("company_domain", ""),
        ]
        # Add tech stack
        tech_stack = lead_data.get("tech_stack", {})
        if tech_stack:
            if isinstance(tech_stack, dict):
                parts.append(str(tech_stack.get("detected_technologies", [])))
            else:
                parts.append(str(tech_stack))

        text = " | ".join(p for p in parts if p)
        return text[:8000]  # Truncate to avoid token limits

    async def _embed_openai(self, lead_id: str, text: str) -> Optional[LeadEmbedding]:
        """Generate embedding using OpenAI API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "text-embedding-3-small",
                        "input": text,
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    vector = data["data"][0]["embedding"]
                    return LeadEmbedding(
                        lead_id=lead_id,
                        vector=vector,
                        model="text-embedding-3-small",
                        dimension=len(vector),
                    )
                else:
                    logger.warning(f"OpenAI embedding error: {resp.status_code}")
        except Exception as e:
            logger.warning(f"OpenAI embedding failed: {e}")

        return None

    def _embed_local(self, lead_id: str, text: str) -> LeadEmbedding:
        """Generate a statistical embedding using character n-gram hashing.

        This is a simple TF-style vector using hashed n-grams.
        Not semantically meaningful but useful for basic similarity.
        """
        vector = self._hash_ngrams(text, self._dimension, n=3)
        return LeadEmbedding(
            lead_id=lead_id,
            vector=vector,
            model="local-ngram-v1",
            dimension=self._dimension,
        )

    def _hash_ngrams(self, text: str, dimensions: int, n: int = 3) -> List[float]:
        """Convert text into a fixed-dimension vector using n-gram hashing."""
        vector = [0.0] * dimensions
        text_lower = text.lower()

        for i in range(len(text_lower) - n + 1):
            ngram = text_lower[i:i + n]
            hash_val = int(hashlib.md5(ngram.encode()).hexdigest(), 16)
            idx = hash_val % dimensions
            # Signed feature: use bit to determine sign
            if (hash_val >> 16) & 1:
                vector[idx] += 1.0
            else:
                vector[idx] -= 1.0

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        dot = sum(av * bv for av, bv in zip(a, b))
        norm_a = math.sqrt(sum(av * av for av in a))
        norm_b = math.sqrt(sum(bv * bv for bv in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# Singleton
embedding_service = EmbeddingService()