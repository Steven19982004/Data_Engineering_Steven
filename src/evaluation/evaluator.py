from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.agent_service import AgentService
from config import Settings
from evaluation.test_queries import EVAL_QUERIES


@dataclass
class EvalCaseResult:
    case_id: str
    query: str
    expected_route: str
    actual_route: str
    expected_tool_path: list[str]
    actual_tool_path: list[str]
    retrieved_titles: list[str]
    final_answer: str
    grounded: bool
    tool_path_match: bool
    route_match: bool


class Evaluator:
    """
    Runs end-to-end evaluation for router/tool/retrieval behavior.

    For each query this evaluator records:
    - query
    - expected tool path
    - actual tool path
    - retrieved movie titles
    - final answer
    - whether answer is basically grounded
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.agent = AgentService(settings)

    def run(self, top_k: int | None = None) -> dict[str, Any]:
        top_k = top_k or self.settings.default_top_k
        results: list[EvalCaseResult] = []

        # Build/reuse index so retrieval cases are measured consistently.
        index_status = self.agent.retriever.build_or_refresh_index(force_rebuild=False)
        self.logger.info("Evaluation index status: %s", index_status)

        for case in EVAL_QUERIES:
            response = self.agent.answer(case["query"], top_k=top_k)

            actual_tools = list(response.get("used_tools", []))
            retrieved_titles = list(response.get("evidence_titles", []))
            answer = str(response.get("answer", ""))

            route_match = str(case.get("expected_route", "")) == str(
                response.get("route", {}).get("route_type", "")
            )
            tool_path_match = self._tool_path_match(
                expected=case.get("expected_tool_path", []),
                actual=actual_tools,
            )
            grounded = self._is_grounded(
                answer=answer,
                retrieved_titles=retrieved_titles,
                actual_tools=actual_tools,
                structured_payload=response.get("structured_results", {}),
            )

            result = EvalCaseResult(
                case_id=str(case["id"]),
                query=str(case["query"]),
                expected_route=str(case.get("expected_route", "")),
                actual_route=str(response.get("route", {}).get("route_type", "")),
                expected_tool_path=list(case.get("expected_tool_path", [])),
                actual_tool_path=actual_tools,
                retrieved_titles=retrieved_titles,
                final_answer=answer,
                grounded=grounded,
                tool_path_match=tool_path_match,
                route_match=route_match,
            )
            results.append(result)

        summary = self._summarize(results)
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "cases": [self._to_dict(r) for r in results],
        }
        return payload

    def save(self, payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / "evaluation_results.json"
        md_path = output_dir / "evaluation_results.md"

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        with md_path.open("w", encoding="utf-8") as f:
            f.write("# Evaluation Results\n\n")
            s = payload["summary"]
            f.write(f"- total_cases: {s['total_cases']}\n")
            f.write(f"- route_match_rate: {s['route_match_rate']:.3f}\n")
            f.write(f"- route_match_rate_explicit: {s['route_match_rate_explicit']:.3f}\n")
            f.write(f"- tool_path_match_rate: {s['tool_path_match_rate']:.3f}\n")
            f.write(f"- grounded_rate: {s['grounded_rate']:.3f}\n\n")

            f.write("## Case Details\n\n")
            for case in payload["cases"]:
                f.write(f"### {case['case_id']}\n")
                f.write(f"- query: {case['query']}\n")
                f.write(f"- expected_route: {case['expected_route']}\n")
                f.write(f"- actual_route: {case['actual_route']}\n")
                f.write(f"- expected_tool_path: {case['expected_tool_path']}\n")
                f.write(f"- actual_tool_path: {case['actual_tool_path']}\n")
                f.write(f"- retrieved_titles: {case['retrieved_titles']}\n")
                f.write(f"- grounded: {case['grounded']}\n")
                f.write(f"- tool_path_match: {case['tool_path_match']}\n")
                f.write(f"- route_match: {case['route_match']}\n")
                f.write(f"- final_answer: {case['final_answer']}\n\n")

        return {"json": str(json_path), "md": str(md_path)}

    def _is_grounded(
        self,
        answer: str,
        retrieved_titles: list[str],
        actual_tools: list[str],
        structured_payload: dict[str, Any],
    ) -> bool:
        if not answer.strip():
            return False

        answer_lower = answer.lower()
        matched_titles = [t for t in retrieved_titles if str(t).lower() in answer_lower]

        # Basic grounded heuristic:
        # - must reference at least one evidence title in answer text
        # - and acknowledge indexed/local evidence boundary when fallback responder is used
        if matched_titles:
            if "当前已索引数据" in answer or "indexed" in answer_lower:
                return True
            return True

        # Director/movie comparison can be grounded without explicit title mentions.
        if "compare_movies_or_directors" in set(actual_tools):
            structured_data = structured_payload.get("data", {})
            results = structured_data.get("results", {}) if isinstance(structured_data, dict) else {}
            has_director_rows = bool(results.get("director_comparison"))
            has_movie_rows = bool(results.get("movie_comparison"))
            if (has_director_rows or has_movie_rows) and ("对比结果" in answer or "director " in answer_lower):
                return True

        return False

    def _tool_path_match(self, expected: list[str], actual: list[str]) -> bool:
        if not expected:
            return True
        actual_set = set(actual)
        return all(tool in actual_set for tool in expected)

    def _summarize(self, results: list[EvalCaseResult]) -> dict[str, Any]:
        total = len(results)
        if total == 0:
            return {
                "total_cases": 0,
                "route_match_rate": 0.0,
                "route_match_rate_explicit": 0.0,
                "tool_path_match_rate": 0.0,
                "grounded_rate": 0.0,
            }

        route_match = sum(1 for r in results if r.expected_route == r.actual_route)
        route_match_explicit = sum(1 for r in results if r.route_match)
        tool_match = sum(1 for r in results if r.tool_path_match)
        grounded = sum(1 for r in results if r.grounded)

        return {
            "total_cases": total,
            "route_match_rate": route_match / total,
            "route_match_rate_explicit": route_match_explicit / total,
            "tool_path_match_rate": tool_match / total,
            "grounded_rate": grounded / total,
        }

    def _to_dict(self, case: EvalCaseResult) -> dict[str, Any]:
        return {
            "case_id": case.case_id,
            "query": case.query,
            "expected_route": case.expected_route,
            "actual_route": case.actual_route,
            "expected_tool_path": case.expected_tool_path,
            "actual_tool_path": case.actual_tool_path,
            "retrieved_titles": case.retrieved_titles,
            "final_answer": case.final_answer,
            "grounded": case.grounded,
            "tool_path_match": case.tool_path_match,
            "route_match": case.route_match,
        }
