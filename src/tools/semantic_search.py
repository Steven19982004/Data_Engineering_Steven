from __future__ import annotations

from typing import Any

from retrieval.retriever import MovieSemanticRetriever


def semantic_movie_search(
    retriever: MovieSemanticRetriever,
    query: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Run semantic retrieval over movie documents."""
    return retriever.semantic_search(query=query, top_k=top_k)
