from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import Settings
from retrieval.embedder import LocalEmbedder
from retrieval.vector_store import MovieVectorStore, VectorItem


@dataclass
class RetrievalResult:
    doc_id: str
    movie_pk: str
    title: str
    release_year: int | None
    director: str | None
    genres: str | None
    source_flags: str | None
    score: float
    snippet: str


class MovieSemanticRetriever:
    """Builds/queries local semantic index from SQLite movie_documents."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

        self.embedder = LocalEmbedder(model_name=settings.embedding_model)
        self.store = MovieVectorStore(persist_dir=settings.vector_db_path)

    def build_or_refresh_index(self, force_rebuild: bool = False) -> dict[str, Any]:
        if force_rebuild:
            self.logger.info("Force rebuilding vector index")
            self.store.reset()

        if self.store.count() > 0 and not force_rebuild:
            return {
                "status": "skipped",
                "reason": "index_exists",
                "count": self.store.count(),
                "backend": self.store.backend,
            }

        rows = self._fetch_documents_from_db()
        if not rows:
            raise RuntimeError(
                "No rows found in movie_documents. Run scripts/run_pipeline.py first."
            )

        embeddings = self.embedder.embed_texts([r["document_text"] for r in rows])

        items: list[VectorItem] = []
        for row, emb in zip(rows, embeddings):
            metadata = dict(row.get("metadata", {}))
            metadata.update(
                {
                    "movie_pk": row.get("movie_pk"),
                    "title": row.get("title"),
                    "release_year": row.get("release_year"),
                    "director": row.get("director"),
                    "genres": row.get("genres"),
                    "source_flags": row.get("source_flags"),
                }
            )
            items.append(
                VectorItem(
                    doc_id=row["doc_id"],
                    document=row["document_text"],
                    embedding=emb,
                    metadata=metadata,
                )
            )

        self.store.upsert(items)
        return {
            "status": "built",
            "count": len(items),
            "embedder_backend": self.embedder.backend,
            "vector_backend": self.store.backend,
        }

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.store.count() == 0:
            self.build_or_refresh_index(force_rebuild=False)

        query_embedding = self.embedder.embed_query(query)
        raw_results = self.store.query(query_embedding=query_embedding, top_k=top_k)

        results: list[dict[str, Any]] = []
        for item in raw_results:
            meta = item.get("metadata", {}) or {}
            doc_text = str(item.get("document", ""))
            results.append(
                {
                    "doc_id": item.get("doc_id"),
                    "movie_pk": meta.get("movie_pk"),
                    "title": meta.get("title"),
                    "release_year": meta.get("release_year"),
                    "director": meta.get("director"),
                    "genres": meta.get("genres"),
                    "source_flags": meta.get("source_flags"),
                    "score": float(item.get("score", 0.0)),
                    "snippet": doc_text[:240],
                }
            )
        return results

    def _fetch_documents_from_db(self) -> list[dict[str, Any]]:
        if not Path(self.settings.sqlite_path).exists():
            raise FileNotFoundError(f"SQLite DB not found: {self.settings.sqlite_path}")

        sql = """
            SELECT
                d.doc_id,
                d.movie_pk,
                d.title,
                d.document_text,
                d.metadata_json,
                m.release_year,
                m.director,
                m.genres,
                m.source_flags
            FROM movie_documents d
            JOIN movies m ON d.movie_pk = m.movie_pk
            ORDER BY d.doc_id;
        """

        with sqlite3.connect(self.settings.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql).fetchall()

        output: list[dict[str, Any]] = []
        for row in rows:
            row_dict = dict(row)
            metadata: dict[str, Any] = {}
            raw_meta = row_dict.get("metadata_json")
            if raw_meta:
                try:
                    metadata = json.loads(raw_meta)
                except Exception:
                    metadata = {}

            output.append(
                {
                    "doc_id": row_dict.get("doc_id"),
                    "movie_pk": row_dict.get("movie_pk"),
                    "title": row_dict.get("title"),
                    "document_text": row_dict.get("document_text", ""),
                    "release_year": row_dict.get("release_year"),
                    "director": row_dict.get("director"),
                    "genres": row_dict.get("genres"),
                    "source_flags": row_dict.get("source_flags"),
                    "metadata": metadata,
                }
            )

        self.logger.info("Loaded %s documents from SQLite for indexing", len(output))
        return output
