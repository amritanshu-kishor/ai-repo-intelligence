"""
Stage 1: Intent Classification
Maps a user query to an orchestration intent for downstream modules.
"""

from __future__ import annotations

import re

from ai.contracts import IntentResult, make_intent_result, new_request_id

VALID_INTENTS = ("impact", "summary", "dependency", "graph", "general")

_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("impact", re.compile(r"\b(impact|affect|break|change|modify|refactor|remove|delete|update|replace)\b", re.I)),
    ("dependency", re.compile(r"\b(depend|package|import|require|coupling)\b", re.I)),
    ("summary", re.compile(r"\b(summar|overview|explain|describe|what does)\b", re.I)),
    ("graph", re.compile(r"\b(graph|path|connected|upstream|downstream|module)\b", re.I)),
]


def classify(query: str, request_id: str | None = None) -> IntentResult:
    """
    Input:  raw user query string
    Output: IntentResult (JSON contract for context_builder)
    """
    rid = request_id or new_request_id()
    query = (query or "").strip()

    if not query:
        return make_intent_result(
            request_id=rid,
            query=query,
            intent="general",
            confidence=0.0,
        )

    scores: dict[str, float] = {name: 0.0 for name in VALID_INTENTS}
    for intent, pattern in _RULES:
        if pattern.search(query):
            scores[intent] += 1.0

    best = max(scores, key=scores.get)
    best_score = scores[best]

    if best_score == 0:
        return make_intent_result(
            request_id=rid,
            query=query,
            intent="general",
            confidence=0.5,
            scores=scores,
        )

    total = sum(scores.values()) or 1.0
    return make_intent_result(
        request_id=rid,
        query=query,
        intent=best,
        confidence=round(best_score / total, 2),
        scores=scores,
    )
