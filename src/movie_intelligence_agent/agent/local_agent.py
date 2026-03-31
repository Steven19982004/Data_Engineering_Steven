from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from movie_intelligence_agent.config import Settings
from movie_intelligence_agent.models import AgentResponse
from movie_intelligence_agent.retrieval.rag import build_theme_summary
from movie_intelligence_agent.tools.movie_tools import MovieTools
from movie_intelligence_agent.tools.sql_tools import SQLTools


@dataclass
class LocalRuleBasedAgent:
    settings: Settings
    sql_tools: SQLTools
    movie_tools: MovieTools

    def ask(self, question: str) -> AgentResponse:
        tool_trace: list[dict[str, Any]] = []
        q = question.strip()
        q_lower = q.lower()

        known_titles = self.movie_tools.list_movie_titles()
        known_directors = self.movie_tools.list_directors()

        if self._looks_like_director_compare(q_lower):
            directors = self._extract_known_directors(q, known_directors)
            if len(directors) < 2:
                directors = ["Christopher Nolan", "Denis Villeneuve"]

            rows = self.sql_tools.compare_directors(directors[0], directors[1])
            tool_trace.append(
                {
                    "tool": "sql.compare_directors",
                    "params": {"director_a": directors[0], "director_b": directors[1]},
                }
            )
            answer = self._format_director_compare(rows, directors)
            return AgentResponse(question=q, answer=answer, tool_trace=tool_trace, mode="local_rule_based")

        if self._looks_like_scifi_filter(q_lower):
            year_from = self._extract_year(q) or 2015
            rows = self.sql_tools.fetch_high_rated_scifi(year_from=year_from, min_rating=7.5, limit=10)
            tool_trace.append(
                {
                    "tool": "sql.fetch_high_rated_scifi",
                    "params": {"year_from": year_from, "min_rating": 7.5, "limit": 10},
                }
            )
            answer = self._format_ranked_movies(
                rows,
                title=f"{year_from} 年后的高评分科幻片",
            )
            return AgentResponse(question=q, answer=answer, tool_trace=tool_trace, mode="local_rule_based")

        if self._looks_like_thriller_filter(q_lower):
            rows = self.sql_tools.fetch_high_quality_thrillers(
                min_rating=7.5,
                min_votes=self.settings.thriller_min_votes,
                limit=10,
            )
            tool_trace.append(
                {
                    "tool": "sql.fetch_high_quality_thrillers",
                    "params": {
                        "min_rating": 7.5,
                        "min_votes": self.settings.thriller_min_votes,
                        "limit": 10,
                    },
                }
            )
            answer = self._format_ranked_movies(rows, title="高评分且高投票数 Thriller 电影")
            return AgentResponse(question=q, answer=answer, tool_trace=tool_trace, mode="local_rule_based")

        if self._looks_like_similarity_query(q_lower):
            titles = self._extract_known_titles(q, known_titles)
            if not titles:
                return AgentResponse(
                    question=q,
                    answer="请在问题中包含一个数据集中存在的电影名，例如 Interstellar。",
                    tool_trace=[],
                    mode="local_rule_based",
                )

            target = titles[0]
            rows = self.movie_tools.find_similar_movies(target, top_k=self.settings.default_top_k)
            tool_trace.append(
                {
                    "tool": "vector.find_similar_movies",
                    "params": {"movie_title": target, "top_k": self.settings.default_top_k},
                }
            )
            answer = self._format_similar_movies(target, rows)
            return AgentResponse(question=q, answer=answer, tool_trace=tool_trace, mode="local_rule_based")

        if self._looks_like_theme_summary(q_lower):
            titles = self._extract_known_titles(q, known_titles)
            if titles:
                payload = self.movie_tools.summarize_common_themes(titles)
                tool_trace.append(
                    {
                        "tool": "nlp.summarize_common_themes",
                        "params": {"movie_titles": titles},
                    }
                )
                answer = (
                    f"匹配电影: {', '.join(payload['matched_titles'])}\n"
                    f"主题总结: {payload['summary']}"
                )
                return AgentResponse(question=q, answer=answer, tool_trace=tool_trace, mode="local_rule_based")

            retrieved = self.movie_tools.retrieve_by_question(q, top_k=self.settings.default_top_k)
            tool_trace.append(
                {
                    "tool": "vector.retrieve_by_question",
                    "params": {"question": q, "top_k": self.settings.default_top_k},
                }
            )
            summary = build_theme_summary([str(r["text"]) for r in retrieved])
            answer = f"未识别到具体电影名，基于相似文本检索结果的主题总结:\n{summary}"
            return AgentResponse(question=q, answer=answer, tool_trace=tool_trace, mode="local_rule_based")

        retrieved = self.movie_tools.retrieve_by_question(q, top_k=self.settings.default_top_k)
        tool_trace.append(
            {
                "tool": "vector.retrieve_by_question",
                "params": {"question": q, "top_k": self.settings.default_top_k},
            }
        )
        answer = self._format_generic_retrieval(retrieved)
        return AgentResponse(question=q, answer=answer, tool_trace=tool_trace, mode="local_rule_based")

    def _looks_like_director_compare(self, q_lower: str) -> bool:
        return ("比较" in q_lower or "compare" in q_lower) and (
            "nolan" in q_lower or "villeneuve" in q_lower or "导演" in q_lower
        )

    def _looks_like_scifi_filter(self, q_lower: str) -> bool:
        return ("科幻" in q_lower or "sci-fi" in q_lower or "science fiction" in q_lower) and (
            "高评分" in q_lower
            or "评分" in q_lower
            or "rated" in q_lower
            or "rating" in q_lower
        )

    def _looks_like_thriller_filter(self, q_lower: str) -> bool:
        return ("thriller" in q_lower or "惊悚" in q_lower) and (
            "投票" in q_lower
            or "votes" in q_lower
            or "高评分" in q_lower
            or "评分" in q_lower
        )

    def _looks_like_similarity_query(self, q_lower: str) -> bool:
        return "相似" in q_lower or "similar" in q_lower

    def _looks_like_theme_summary(self, q_lower: str) -> bool:
        return "主题" in q_lower or "总结" in q_lower or "theme" in q_lower or "summar" in q_lower

    def _extract_year(self, text: str) -> int | None:
        m = re.search(r"(19|20)\d{2}", text)
        return int(m.group()) if m else None

    def _extract_known_titles(self, text: str, known_titles: list[str]) -> list[str]:
        text_lower = text.lower()
        return [title for title in known_titles if title.lower() in text_lower]

    def _extract_known_directors(self, text: str, known_directors: list[str]) -> list[str]:
        text_lower = text.lower()
        return [d for d in known_directors if d and d.lower() in text_lower]

    def _format_ranked_movies(self, rows: list[dict[str, Any]], title: str) -> str:
        if not rows:
            return f"{title}: 没有匹配结果。"

        lines = [f"{title}:" ]
        for i, row in enumerate(rows, 1):
            lines.append(
                f"{i}. {row['title']} ({row['release_year']}) | rating={row['imdb_rating']} | votes={row['vote_count']} | director={row['director']}"
            )
        return "\n".join(lines)

    def _format_director_compare(self, rows: list[dict[str, Any]], directors: list[str]) -> str:
        if not rows:
            return f"未找到导演 {directors[0]} 与 {directors[1]} 的可比较数据。"

        lines = ["导演表现对比:"]
        for row in rows:
            lines.append(
                f"- {row['director']}: movies={row['movie_count']}, avg_rating={row['avg_rating']}, best_rating={row['best_rating']}, total_votes={row['total_votes']}"
            )
        return "\n".join(lines)

    def _format_similar_movies(self, target: str, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return f"没有找到与 {target} 相似的电影。"

        lines = [f"与 {target} 相似的电影:"]
        for i, row in enumerate(rows, 1):
            lines.append(f"{i}. {row['title']} (score={row['score']})")
        return "\n".join(lines)

    def _format_generic_retrieval(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "未检索到相关电影。"

        lines = ["根据语义检索到的相关电影:"]
        for i, row in enumerate(rows, 1):
            lines.append(f"{i}. {row['title']} (score={row['score']})")
        return "\n".join(lines)
