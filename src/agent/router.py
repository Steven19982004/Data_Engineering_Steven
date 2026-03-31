from __future__ import annotations

from dataclasses import dataclass, asdict
import re


STRUCTURED_KEYWORDS = {
    "filter",
    "top",
    "highest",
    "rating",
    "vote",
    "year",
    "after",
    "before",
    "compare",
    "count",
    "排名",
    "筛选",
    "评分",
    "投票",
    "年份",
    "之后",
    "之前",
    "比较",
    "统计",
    "导演",
    "recommend",
    "recommended",
    "best",
    "worth",
    "高分",
    "年后",
    "年之前",
    "之后",
    "以前",
    "推荐",
    "值得看",
    "最值得",
}

SEMANTIC_KEYWORDS = {
    "similar",
    "similarity",
    "theme",
    "style",
    "tone",
    "motif",
    "summary",
    "summarize",
    "semantic",
    "like",
    "related",
    "plot",
    "相似",
    "主题",
    "风格",
    "总结",
    "语义",
    "文本",
    "类似",
    "接近",
    "共同主题",
    "相近",
}


@dataclass
class RoutingDecision:
    route_type: str
    use_structured: bool
    use_semantic: bool
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


_YEAR_PATTERN = re.compile(r"(19|20)\d{2}")
_TEMPORAL_KEYWORDS = {
    "year",
    "after",
    "before",
    "since",
    "from",
    "post",
    "pre",
    "年",
    "之后",
    "以前",
    "后",
    "前",
}


def _has_structured_signal(q: str) -> bool:
    """
    Structured intent signals:
    - filter/rank/compare style keywords
    - explicit year constraints (e.g., 2015, 2010 年后)
    """
    has_keyword = any(k in q for k in STRUCTURED_KEYWORDS)
    has_year = bool(_YEAR_PATTERN.search(q))
    has_temporal_context = any(k in q for k in _TEMPORAL_KEYWORDS)
    return has_keyword or (has_year and has_temporal_context)


def _has_semantic_signal(q: str) -> bool:
    """
    Semantic intent signals:
    - similarity/theme/summarization style keywords
    """
    return any(k in q for k in SEMANTIC_KEYWORDS)


def route_query(query: str) -> RoutingDecision:
    q = (query or "").lower()

    structured_hit = _has_structured_signal(q)
    semantic_hit = _has_semantic_signal(q)

    if structured_hit and semantic_hit:
        return RoutingDecision(
            route_type="hybrid",
            use_structured=True,
            use_semantic=True,
            rationale="Detected both analytical and semantic intent.",
        )

    if structured_hit:
        return RoutingDecision(
            route_type="structured",
            use_structured=True,
            use_semantic=False,
            rationale="Detected filter/sort/compare intent.",
        )

    if semantic_hit:
        return RoutingDecision(
            route_type="semantic",
            use_structured=False,
            use_semantic=True,
            rationale="Detected similarity/theme/summary intent.",
        )

    # Default to hybrid to maximize evidence coverage for ambiguous questions.
    return RoutingDecision(
        route_type="hybrid",
        use_structured=True,
        use_semantic=True,
        rationale="Ambiguous query: running both structured and semantic tools.",
    )
