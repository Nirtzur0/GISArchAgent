"""
Embedding functions for ChromaDB.

We default to a deterministic local embedding for testability and to avoid
implicit model downloads at runtime. For production-grade semantic search,
swap this for OpenAI / sentence-transformers embeddings explicitly.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import List


class DeterministicHashEmbeddingFunction:
    """A tiny, dependency-free embedding function (bag-of-words hashing).

    This is not "semantic". It is intended for:
    - fast local development
    - deterministic tests
    - environments where downloading embedding models is undesirable

    It works well enough for keyword overlap and multilingual exact-token matches.
    """

    def __init__(self, dim: int = 128):
        if dim <= 0:
            raise ValueError("dim must be > 0")
        self.dim = dim

    @staticmethod
    def name() -> str:
        # Stable identifier used by Chroma to detect embedding-function conflicts.
        return "gisarch_deterministic_hash_v1"

    def get_config(self) -> dict:
        return {"dim": self.dim}

    @staticmethod
    def build_from_config(config: dict) -> "DeterministicHashEmbeddingFunction":
        dim = int((config or {}).get("dim", 128))
        return DeterministicHashEmbeddingFunction(dim=dim)

    def __call__(self, input: List[str]) -> List[List[float]]:
        return [self._embed_one(t or "") for t in input]

    def embed_query(self, input: str | List[str]) -> List[List[float]]:
        # Chroma may call embed_query with either a string or list[str].
        if isinstance(input, str):
            return self([input])
        return self(input)

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self(input)

    def _embed_one(self, text: str) -> List[float]:
        vec = [0.0] * self.dim

        # Tokenize: keep Hebrew/Latin letters + digits; split on everything else.
        tokens = re.findall(r"[0-9A-Za-z\u0590-\u05FF]+", text.lower())
        if not tokens:
            return vec

        for tok in tokens:
            h = hashlib.md5(tok.encode("utf-8")).digest()
            idx = int.from_bytes(h[:4], "little") % self.dim
            sign = -1.0 if (h[4] & 1) else 1.0
            vec[idx] += sign

        # L2 normalize to make cosine-ish distances less sensitive to length.
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec
