from __future__ import annotations

import json
import time
from dataclasses import asdict

from movie_intelligence_agent.agent.runner import MovieIntelligenceAgent
from movie_intelligence_agent.config import Settings
from movie_intelligence_agent.logger import configure_logging, get_logger
from movie_intelligence_agent.models import EvaluationResult


def run_evaluation(settings: Settings, force_local: bool = True) -> dict:
    settings.ensure_directories()
    configure_logging(settings.log_path)
    logger = get_logger("evaluation")

    with settings.eval_data_path.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    agent = MovieIntelligenceAgent(settings=settings, force_local=force_local)

    results: list[EvaluationResult] = []

    for case in cases:
        start = time.perf_counter()
        response = agent.ask(case["question"])
        latency_ms = (time.perf_counter() - start) * 1000

        used_tools = [t["tool"] for t in response.tool_trace]
        tool_match = case["expected_tool"] in used_tools

        answer_lower = response.answer.lower()
        expected_keywords = case.get("expected_keywords", [])
        keyword_hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)

        result = EvaluationResult(
            case_id=case["id"],
            question=case["question"],
            expected_tool=case["expected_tool"],
            used_tools=used_tools,
            tool_match=tool_match,
            keyword_hits=keyword_hits,
            keyword_total=len(expected_keywords),
            latency_ms=round(latency_ms, 2),
            answer_preview=response.answer[:220],
        )
        results.append(result)

    tool_match_rate = round(sum(r.tool_match for r in results) / max(len(results), 1), 3)
    keyword_hit_rate = round(
        sum(r.keyword_hits for r in results) / max(sum(r.keyword_total for r in results), 1), 3
    )
    avg_latency_ms = round(sum(r.latency_ms for r in results) / max(len(results), 1), 2)

    report = {
        "summary": {
            "total_cases": len(results),
            "tool_match_rate": tool_match_rate,
            "keyword_hit_rate": keyword_hit_rate,
            "avg_latency_ms": avg_latency_ms,
            "agent_mode": agent.mode,
        },
        "cases": [asdict(r) for r in results],
    }

    json_path = settings.output_dir / "evaluation_report.json"
    md_path = settings.output_dir / "evaluation_report.md"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Evaluation Report\n\n")
        f.write(f"- total_cases: {report['summary']['total_cases']}\n")
        f.write(f"- tool_match_rate: {report['summary']['tool_match_rate']}\n")
        f.write(f"- keyword_hit_rate: {report['summary']['keyword_hit_rate']}\n")
        f.write(f"- avg_latency_ms: {report['summary']['avg_latency_ms']}\n")
        f.write(f"- agent_mode: {report['summary']['agent_mode']}\n\n")
        f.write("## Case Details\n\n")
        for item in report["cases"]:
            f.write(f"### {item['case_id']}\n")
            f.write(f"- question: {item['question']}\n")
            f.write(f"- expected_tool: {item['expected_tool']}\n")
            f.write(f"- used_tools: {item['used_tools']}\n")
            f.write(f"- tool_match: {item['tool_match']}\n")
            f.write(
                f"- keyword_hits: {item['keyword_hits']}/{item['keyword_total']}\n"
            )
            f.write(f"- latency_ms: {item['latency_ms']}\n")
            f.write(f"- answer_preview: {item['answer_preview']}\n\n")

    logger.info("Evaluation complete. JSON=%s MD=%s", json_path, md_path)
    return report
