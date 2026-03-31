from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd


logger = logging.getLogger("build_documents")


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_movie_documents(movies_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build one embedding-ready document per movie.

    Document text combines:
    - title
    - genres
    - overview
    - tagline
    - review snippet
    """
    if movies_df.empty:
        raise ValueError("Cannot build documents from empty movies DataFrame")

    rows: list[dict[str, Any]] = []
    for _, row in movies_df.iterrows():
        movie_pk = _safe_text(row.get("movie_pk"))
        title = _safe_text(row.get("title"))
        genres = _safe_text(row.get("genres"))
        overview = _safe_text(row.get("overview"))
        tagline = _safe_text(row.get("tagline"))
        review_snippet = _safe_text(row.get("review_snippet"))

        document_text = "\n".join(
            [
                f"Title: {title}",
                f"Genres: {genres}",
                f"Overview: {overview}",
                f"Tagline: {tagline}",
                f"Review snippet: {review_snippet}",
            ]
        ).strip()

        metadata = {
            "movie_pk": movie_pk,
            "title": title,
            "release_year": int(row.get("release_year")),
            "director": _safe_text(row.get("director")),
            "genres": genres,
            "source_flags": _safe_text(row.get("source_flags")),
        }

        rows.append(
            {
                "doc_id": f"doc_{movie_pk}",
                "movie_pk": movie_pk,
                "title": title,
                "document_text": document_text,
                "metadata_json": json.dumps(metadata, ensure_ascii=False),
            }
        )

    docs_df = pd.DataFrame(rows)
    logger.info("Built %s movie documents", len(docs_df))
    return docs_df
