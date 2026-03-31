from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResponse:
    question: str
    answer: str
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "unknown"


@dataclass
class EvaluationResult:
    case_id: str
    question: str
    expected_tool: str
    used_tools: list[str]
    tool_match: bool
    keyword_hits: int
    keyword_total: int
    latency_ms: float
    answer_preview: str
