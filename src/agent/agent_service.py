from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from typing import Any

from agent.prompts import SYSTEM_PROMPT, build_llm_user_prompt
from agent.router import route_query
from config import Settings
from retrieval.retriever import MovieSemanticRetriever
from tools.compare_movies import compare_movies_or_directors
from tools.search_movies import search_movies_by_filters
from tools.semantic_search import semantic_movie_search
from tools.top_rated import get_top_rated_movies


class AgentService:
    """Lightweight tool-based agent service with LLM optionality."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db_path = Path(settings.sqlite_path)
        self.retriever = MovieSemanticRetriever(settings)

    def answer(self, query: str, top_k: int | None = None) -> dict[str, Any]:
        top_k = top_k or self.settings.default_top_k
        routing = route_query(query)

        used_tools: list[str] = []
        structured_payload: dict[str, Any] = {"tool": None, "data": []}
        semantic_payload: list[dict[str, Any]] = []

        if routing.use_structured:
            structured_payload = self._run_structured_tools(query=query, top_k=top_k)
            if structured_payload.get("tool"):
                used_tools.append(str(structured_payload["tool"]))

        if routing.use_semantic:
            semantic_payload = semantic_movie_search(
                retriever=self.retriever,
                query=query,
                top_k=top_k,
            )
            used_tools.append("semantic_movie_search")

        evidence_titles = self._collect_evidence_titles(structured_payload, semantic_payload)

        llm_answer = None
        if self.settings.use_real_llm and self.settings.openai_api_key:
            llm_answer = self._try_llm_answer(
                query=query,
                routing=routing.to_dict(),
                structured_payload=structured_payload,
                semantic_payload=semantic_payload,
            )

        answer_text = llm_answer or self._deterministic_fallback_answer(
            query=query,
            routing=routing.to_dict(),
            structured_payload=structured_payload,
            semantic_payload=semantic_payload,
            evidence_titles=evidence_titles,
        )

        return {
            "query": query,
            "route": routing.to_dict(),
            "used_tools": used_tools,
            "answer": answer_text,
            "evidence_titles": evidence_titles,
            "structured_results": structured_payload,
            "semantic_results": semantic_payload,
        }

    def _run_structured_tools(self, query: str, top_k: int) -> dict[str, Any]:
        q = query.lower()
        directors = self._extract_directors_from_query(query)
        titles = self._extract_titles_from_query(query)
        year_from = self._extract_year(query)
        genre = self._extract_genre(query)

        compare_keywords = {
            "compare",
            "比较",
            "vs",
            "versus",
            "performance",
            "表现",
            "filmography",
            "作品",
        }
        director_analysis_keywords = {
            "导演",
            "director",
            "movie",
            "电影",
            "worth",
            "值得看",
            "推荐",
            "best",
        }

        # Compare intent:
        # 1) explicit compare/vs keywords
        # 2) director-focused analytical requests (even without "compare")
        compare_intent = any(k in q for k in compare_keywords) or (
            bool(directors) and any(k in q for k in director_analysis_keywords)
        )
        if compare_intent:
            payload = compare_movies_or_directors(
                db_path=self.db_path,
                directors=directors,
                movie_titles=titles,
                year_from=year_from,
            )
            return {"tool": "compare_movies_or_directors", "data": payload}

        # Top/high-rated intent
        top_keywords = {
            "top",
            "highest",
            "高评分",
            "高分",
            "最高",
            "top rated",
            "评分",
            "best",
            "worth",
            "值得看",
            "推荐",
        }
        if any(k in q for k in top_keywords):
            payload = get_top_rated_movies(
                db_path=self.db_path,
                genre=genre,
                year_from=year_from,
                min_votes=self.settings.min_vote_count,
                limit=top_k,
            )
            return {"tool": "get_top_rated_movies", "data": payload}

        # Generic filtered search
        payload = search_movies_by_filters(
            db_path=self.db_path,
            title_contains=self._extract_title_keyword(query),
            year_from=year_from,
            genres=[genre] if genre else None,
            min_rating=self.settings.high_rating_threshold if ("高评分" in q or "top" in q) else None,
            min_votes=self.settings.min_vote_count if ("投票" in q or "vote" in q) else None,
            limit=top_k,
        )
        return {"tool": "search_movies_by_filters", "data": payload}

    def _collect_evidence_titles(
        self,
        structured_payload: dict[str, Any],
        semantic_payload: list[dict[str, Any]],
    ) -> list[str]:
        titles: list[str] = []

        s_data = structured_payload.get("data")
        if isinstance(s_data, list):
            for item in s_data:
                title = item.get("title")
                if title:
                    titles.append(str(title))
        elif isinstance(s_data, dict):
            for key in ["movie_comparison", "director_comparison"]:
                arr = s_data.get("results", {}).get(key, [])
                for item in arr:
                    title = item.get("title")
                    if title:
                        titles.append(str(title))

        for item in semantic_payload:
            title = item.get("title")
            if title:
                titles.append(str(title))

        # stable dedup order
        seen = set()
        output = []
        for t in titles:
            if t not in seen:
                seen.add(t)
                output.append(t)
        return output

    def _deterministic_fallback_answer(
        self,
        query: str,
        routing: dict[str, Any],
        structured_payload: dict[str, Any],
        semantic_payload: list[dict[str, Any]],
        evidence_titles: list[str],
    ) -> str:
        lines: list[str] = []
        lines.append("基于当前已索引数据，我给出以下结果（deterministic fallback）：")
        lines.append(f"- Routing: {routing.get('route_type')} ({routing.get('rationale')})")

        tool_name = structured_payload.get("tool")
        data = structured_payload.get("data")

        if tool_name:
            lines.append(f"- Structured tool: {tool_name}")

        if isinstance(data, list) and data:
            lines.append("- 结构化结果:")
            for i, item in enumerate(data[:8], 1):
                lines.append(
                    f"  {i}. {item.get('title')} ({item.get('release_year')}) | "
                    f"rating={item.get('imdb_rating')} | votes={item.get('vote_count')} | "
                    f"source={item.get('source_flags')}"
                )
        elif isinstance(data, dict) and data:
            lines.append("- 对比结果:")
            director_rows = data.get("results", {}).get("director_comparison", [])
            movie_rows = data.get("results", {}).get("movie_comparison", [])
            for row in director_rows:
                lines.append(
                    f"  - Director {row.get('director')}: movies={row.get('movie_count')}, "
                    f"avg_rating={row.get('avg_rating')}, total_votes={row.get('total_votes')}"
                )
            for row in movie_rows:
                lines.append(
                    f"  - Movie {row.get('title')} ({row.get('release_year')}): "
                    f"rating={row.get('imdb_rating')}, votes={row.get('vote_count')}"
                )
        else:
            lines.append("- 结构化结果为空。")

        if semantic_payload:
            lines.append("- 语义检索结果:")
            for i, hit in enumerate(semantic_payload[:8], 1):
                lines.append(
                    f"  {i}. {hit.get('title')} ({hit.get('release_year')}) | "
                    f"score={hit.get('score')} | source={hit.get('source_flags')}"
                )

        if evidence_titles:
            lines.append(f"- 证据电影: {', '.join(evidence_titles[:12])}")
        else:
            lines.append("- 没有足够证据电影命中。")

        lines.append("注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。")
        return "\n".join(lines)

    def _try_llm_answer(
        self,
        query: str,
        routing: dict[str, Any],
        structured_payload: dict[str, Any],
        semantic_payload: list[dict[str, Any]],
    ) -> str | None:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            self.logger.warning("OpenAI SDK unavailable, fallback responder will be used: %s", exc)
            return None

        try:
            client = OpenAI(api_key=self.settings.openai_api_key)
            user_prompt = build_llm_user_prompt(
                query=query,
                routing=routing,
                structured_payload=structured_payload,
                semantic_payload=semantic_payload,
            )
            completion = client.chat.completions.create(
                model=self.settings.llm_model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return completion.choices[0].message.content
        except Exception as exc:
            self.logger.warning("LLM call failed, fallback responder will be used: %s", exc)
            return None

    def _extract_year(self, query: str) -> int | None:
        m = re.search(r"(19|20)\d{2}", query)
        return int(m.group()) if m else None

    def _extract_genre(self, query: str) -> str | None:
        q = query.lower()
        mapping = {
            "科幻": "Sci-Fi",
            "sci-fi": "Sci-Fi",
            "science fiction": "Sci-Fi",
            "thriller": "Thriller",
            "惊悚": "Thriller",
            "drama": "Drama",
            "剧情": "Drama",
            "crime": "Crime",
            "犯罪": "Crime",
            "horror": "Horror",
            "恐怖": "Horror",
            "mystery": "Mystery",
            "悬疑": "Mystery",
            "action": "Action",
            "动作": "Action",
            "adventure": "Adventure",
            "冒险": "Adventure",
            "comedy": "Comedy",
            "喜剧": "Comedy",
            "history": "History",
            "历史": "History",
        }
        for k, v in mapping.items():
            if k in q:
                return v
        return None

    def _extract_title_keyword(self, query: str) -> str | None:
        # Try quoted phrase first.
        m = re.search(r'"([^"]+)"', query)
        if m:
            return m.group(1)

        # Otherwise return None to avoid over-filtering.
        return None

    def _extract_directors_from_query(self, query: str) -> list[str]:
        known = self._load_known_values("director")
        q = query.lower()
        return [d for d in known if d and d.lower() in q]

    def _extract_titles_from_query(self, query: str) -> list[str]:
        known = self._load_known_values("title")
        q = query.lower()
        # Longest title first to reduce nested-match ambiguity.
        known_sorted = sorted(known, key=len, reverse=True)
        output = []
        for title in known_sorted:
            if title and title.lower() in q:
                output.append(title)
        return output

    def _load_known_values(self, column: str) -> list[str]:
        if column not in {"title", "director"}:
            return []

        if not self.db_path.exists():
            return []

        sql = f"SELECT DISTINCT {column} AS value FROM movies WHERE {column} IS NOT NULL ORDER BY {column};"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql).fetchall()
        return [str(r["value"]) for r in rows if r["value"]]
