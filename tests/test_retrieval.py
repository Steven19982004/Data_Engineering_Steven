from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config import Settings
from retrieval.retriever import MovieSemanticRetriever


ROOT_DIR = Path(__file__).resolve().parents[1]


def _run_pipeline() -> None:
    subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "run_pipeline.py")],
        cwd=str(ROOT_DIR),
        check=True,
    )


def test_retrieval_builds_index_and_returns_hits() -> None:
    _run_pipeline()
    settings = Settings.from_env()

    retriever = MovieSemanticRetriever(settings)
    build_status = retriever.build_or_refresh_index(force_rebuild=True)

    assert build_status["status"] in {"built", "skipped"}
    assert build_status.get("count", 0) >= 10

    hits = retriever.semantic_search("movies similar to Interstellar and Arrival", top_k=5)
    assert len(hits) > 0

    sample = hits[0]
    assert "title" in sample
    assert "score" in sample
    assert "source_flags" in sample
