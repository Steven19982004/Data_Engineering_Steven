from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """
You are a grounded movie intelligence assistant.
You must answer ONLY from provided tool evidence.
If evidence is weak or incomplete, explicitly say so.
Do not hallucinate facts.
Always mention supporting movie titles in your final answer.
""".strip()


def build_llm_user_prompt(
    query: str,
    routing: dict[str, Any],
    structured_payload: dict[str, Any],
    semantic_payload: list[dict[str, Any]],
) -> str:
    context = {
        "query": query,
        "routing": routing,
        "structured_payload": structured_payload,
        "semantic_payload": semantic_payload,
    }
    return (
        "User question:\n"
        f"{query}\n\n"
        "Evidence from tools (JSON):\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "Write a concise, grounded answer in the same language as the user query."
    )
