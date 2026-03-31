from __future__ import annotations

import re
from collections import Counter


_STOP_WORDS = {
    "the",
    "and",
    "with",
    "for",
    "that",
    "this",
    "into",
    "from",
    "about",
    "while",
    "where",
    "through",
    "film",
    "movie",
    "story",
    "themes",
    "theme",
}


def extract_theme_keywords(texts: list[str], top_n: int = 6) -> list[str]:
    tokens: list[str] = []
    for text in texts:
        words = re.findall(r"[a-zA-Z]{3,}", text.lower())
        tokens.extend([w for w in words if w not in _STOP_WORDS])

    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_n)]


def build_theme_summary(texts: list[str]) -> str:
    keywords = extract_theme_keywords(texts, top_n=6)
    if not keywords:
        return "Insufficient context to infer clear themes."

    return (
        "Common themes observed across retrieved descriptions/reviews include: "
        + ", ".join(keywords)
        + "."
    )
