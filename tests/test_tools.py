from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config import Settings
from tools.compare_movies import compare_movies_or_directors
from tools.search_movies import search_movies_by_filters
from tools.top_rated import get_top_rated_movies


ROOT_DIR = Path(__file__).resolve().parents[1]


def _run_pipeline() -> None:
    subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "run_pipeline.py")],
        cwd=str(ROOT_DIR),
        check=True,
    )


def test_top_rated_tool_returns_ranked_results() -> None:
    _run_pipeline()
    settings = Settings.from_env()

    rows = get_top_rated_movies(
        db_path=settings.sqlite_path,
        genre="Sci-Fi",
        year_from=2015,
        min_votes=100000,
        limit=5,
    )

    assert len(rows) > 0
    assert all(r["release_year"] >= 2015 for r in rows)
    assert all("Sci-Fi" in (r.get("genres") or "") for r in rows)


def test_search_movies_by_filters_returns_non_empty_for_known_filters() -> None:
    _run_pipeline()
    settings = Settings.from_env()

    rows = search_movies_by_filters(
        db_path=settings.sqlite_path,
        genres=["Thriller"],
        min_rating=7.5,
        min_votes=100000,
        limit=10,
    )

    assert len(rows) > 0
    assert all((r.get("imdb_rating") or 0) >= 7.5 for r in rows)


def test_compare_movies_or_directors_returns_director_aggregation() -> None:
    _run_pipeline()
    settings = Settings.from_env()

    payload = compare_movies_or_directors(
        db_path=settings.sqlite_path,
        directors=["Christopher Nolan", "Denis Villeneuve"],
    )

    assert payload["mode"] in {"director", "mixed"}
    director_rows = payload.get("results", {}).get("director_comparison", [])
    assert len(director_rows) >= 2
