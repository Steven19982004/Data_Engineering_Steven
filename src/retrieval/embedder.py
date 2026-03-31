from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Iterable


_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9\u4e00-\u9fff]+")


@dataclass
class LocalEmbedder:
    """
    Embedding wrapper with graceful fallback.

    Preferred path:
    - sentence-transformers model embeddings (semantic quality higher)

    Fallback path (deterministic, no external dependency):
    - hashed bag-of-words vector
    """

    model_name: str = "all-MiniLM-L6-v2"
    fallback_dim: int = 384

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._model = None
        self._backend = "hash_fallback"

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self.model_name)
            self._backend = "sentence_transformers"
            self.logger.info("Embedder backend: sentence-transformers (%s)", self.model_name)
        except Exception as exc:
            self.logger.warning(
                "sentence-transformers unavailable, using deterministic hash fallback. error=%s",
                exc,
            )

    @property
    def backend(self) -> str:
        return self._backend

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        text_list = [str(t or "") for t in texts]
        if not text_list:
            return []

        if self._backend == "sentence_transformers" and self._model is not None:
            vectors = self._model.encode(text_list, normalize_embeddings=True)
            return [list(map(float, vec)) for vec in vectors]

        return [self._hash_embed(text) for text in text_list]

    def embed_query(self, query: str) -> list[float]:
        vectors = self.embed_texts([query])
        return vectors[0] if vectors else []

    def _hash_embed(self, text: str) -> list[float]:
        vector = [0.0] * self.fallback_dim
        tokens = _TOKEN_PATTERN.findall(text.lower())

        if not tokens:
            return vector

        for token in tokens:
            idx = hash(token) % self.fallback_dim
            vector[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector
