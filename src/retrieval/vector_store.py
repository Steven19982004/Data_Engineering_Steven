from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class VectorItem:
    doc_id: str
    document: str
    embedding: list[float]
    metadata: dict[str, Any]


class MovieVectorStore:
    """
    Local vector store with two backends:
    1) Chroma persistent DB (preferred)
    2) JSON fallback store (if chromadb unavailable)
    """

    def __init__(self, persist_dir: Path, collection_name: str = "movie_documents") -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        self._backend = "json_fallback"
        self._json_path = self.persist_dir / f"{collection_name}_vectors.json"
        self._fallback_records: dict[str, dict[str, Any]] = {}

        self._chroma_client = None
        self._chroma_collection = None

        try:
            import chromadb  # type: ignore

            self._chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._backend = "chroma"
            self.logger.info("Vector store backend: chroma (%s)", self.persist_dir)
        except Exception as exc:
            self.logger.warning(
                "chromadb unavailable, using JSON fallback store. error=%s", exc
            )
            self._load_fallback()

    @property
    def backend(self) -> str:
        return self._backend

    def reset(self) -> None:
        if self._backend == "chroma" and self._chroma_client is not None:
            try:
                self._chroma_client.delete_collection(self.collection_name)
            except Exception:
                pass
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            return

        self._fallback_records = {}
        self._save_fallback()

    def count(self) -> int:
        if self._backend == "chroma" and self._chroma_collection is not None:
            return int(self._chroma_collection.count())
        return len(self._fallback_records)

    def upsert(self, items: list[VectorItem]) -> None:
        if not items:
            return

        if self._backend == "chroma" and self._chroma_collection is not None:
            self._chroma_collection.upsert(
                ids=[item.doc_id for item in items],
                documents=[item.document for item in items],
                metadatas=[item.metadata for item in items],
                embeddings=[item.embedding for item in items],
            )
            return

        for item in items:
            self._fallback_records[item.doc_id] = {
                "doc_id": item.doc_id,
                "document": item.document,
                "embedding": item.embedding,
                "metadata": item.metadata,
            }
        self._save_fallback()

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []

        if self._backend == "chroma" and self._chroma_collection is not None:
            payload = self._chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            ids = payload.get("ids", [[]])[0]
            docs = payload.get("documents", [[]])[0]
            metas = payload.get("metadatas", [[]])[0]
            distances = payload.get("distances", [[]])[0]

            results: list[dict[str, Any]] = []
            for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
                distance = float(dist) if dist is not None else 1.0
                similarity = 1.0 - distance
                results.append(
                    {
                        "doc_id": doc_id,
                        "document": doc,
                        "metadata": meta or {},
                        "score": round(similarity, 4),
                    }
                )
            return results

        # Fallback backend query
        scored: list[tuple[float, dict[str, Any]]] = []
        for record in self._fallback_records.values():
            score = self._cosine_similarity(query_embedding, record.get("embedding", []))
            scored.append((score, record))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, record in scored[:top_k]:
            results.append(
                {
                    "doc_id": record.get("doc_id"),
                    "document": record.get("document", ""),
                    "metadata": record.get("metadata", {}),
                    "score": round(float(score), 4),
                }
            )
        return results

    def _load_fallback(self) -> None:
        if not self._json_path.exists():
            self._fallback_records = {}
            return

        with self._json_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        self._fallback_records = {
            item["doc_id"]: item for item in payload.get("records", []) if "doc_id" in item
        }

    def _save_fallback(self) -> None:
        payload = {"records": list(self._fallback_records.values())}
        with self._json_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0

        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        return dot / (n1 * n2)
