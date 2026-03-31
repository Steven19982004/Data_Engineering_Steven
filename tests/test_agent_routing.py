from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agent.agent_service import AgentService
from config import Settings


ROOT_DIR = Path(__file__).resolve().parents[1]


def _run_pipeline() -> None:
    subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "run_pipeline.py")],
        cwd=str(ROOT_DIR),
        check=True,
    )


def test_hybrid_query_uses_structured_and_semantic_tools() -> None:
    _run_pipeline()
    settings = Settings.from_env()
    service = AgentService(settings)

    response = service.answer("推荐和 Dune: Part Two 类似的高评分科幻电影", top_k=5)

    assert response["route"]["route_type"] == "hybrid"
    assert "get_top_rated_movies" in response["used_tools"]
    assert "semantic_movie_search" in response["used_tools"]


def test_director_plus_style_query_routes_to_hybrid_with_compare_tool() -> None:
    _run_pipeline()
    settings = Settings.from_env()
    service = AgentService(settings)

    response = service.answer(
        "2010 年后 Denis Villeneuve 的电影里，哪些最值得看并且风格接近 Arrival",
        top_k=5,
    )

    assert response["route"]["route_type"] == "hybrid"
    assert "compare_movies_or_directors" in response["used_tools"]
    assert "semantic_movie_search" in response["used_tools"]
