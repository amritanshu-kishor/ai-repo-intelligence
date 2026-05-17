"""
Phase 2: Impact analysis from graph traversal + dependency metadata.
Estimates severity, propagation scope, and explainable risk levels.

Future: populate ai_reasoning via IBM watsonx orchestration agent.
"""

from __future__ import annotations

from typing import Any

from ai.contracts import ContextResult, GraphResult, ImpactResult, make_impact_result


def _propagation_depth_from_graph(graph: GraphResult) -> int:
    return int(graph.get("propagation_depth", 0) or 0)


def _propagation_scope(
    focus: str | None,
    direct: list[str],
    indirect: list[str],
    upstream: list[str],
) -> dict[str, Any]:
    total = len({focus, *direct, *indirect, *upstream}) - (0 if focus else 1)
    return {
        "total_affected": max(total, 0),
        "direct_count": len(direct),
        "indirect_count": len(indirect),
        "upstream_count": len(upstream),
        "focus_node_id": focus,
    }


def _impact_severity(risk_score: float, propagation_depth: int, cycle_count: int) -> str:
    if risk_score >= 0.75 or cycle_count > 0 and propagation_depth >= 2:
        return "critical"
    if risk_score >= 0.5 or propagation_depth >= 2:
        return "high"
    if risk_score >= 0.3 or propagation_depth >= 1:
        return "medium"
    return "low"


def _collect_risk_flags(context: ContextResult, affected_ids: set[str]) -> list[str]:
    deps = context.get("data", {}).get("dependencies") or {}
    if not isinstance(deps, dict):
        return ["Dependency metadata unavailable or malformed."]
    factors: list[str] = []
    for flag in deps.get("risk_flags") or []:
        if not isinstance(flag, dict):
            continue
        module = str(flag.get("module", ""))
        if any(aid in module or module in aid for aid in affected_ids):
            factors.append(
                f"{flag.get('severity', 'unknown')}: {flag.get('issue', 'flagged module')}"
            )
    return factors


def _score_risk(
    propagation_depth: int,
    affected_count: int,
    cycle_count: int,
    flag_count: int,
) -> tuple[float, str]:
    score = min(
        1.0,
        propagation_depth * 0.15
        + affected_count * 0.08
        + cycle_count * 0.25
        + flag_count * 0.12,
    )
    if score >= 0.65:
        level = "high"
    elif score >= 0.35:
        level = "medium"
    else:
        level = "low"
    return round(score, 2), level


def _risk_explanation(
    severity: str,
    scope: dict[str, Any],
    risk_factors: list[str],
    graph: GraphResult,
) -> str:
    narrative = graph.get("reasoning_summary", {}).get("narrative", "")
    factors = "; ".join(risk_factors[:3]) if risk_factors else "no additional flags"
    return (
        f"Impact severity is {severity} with {scope.get('total_affected', 0)} modules in scope "
        f"(direct={scope.get('direct_count', 0)}, indirect={scope.get('indirect_count', 0)}, "
        f"upstream={scope.get('upstream_count', 0)}). {narrative} Risk factors: {factors}."
    )


def _empty_impact(request_id: str, reason: str) -> ImpactResult:
    return make_impact_result(
        request_id=request_id,
        propagation_depth=0,
        propagation_scope={"total_affected": 0, "direct_count": 0, "indirect_count": 0, "upstream_count": 0},
        impact_severity="low",
        risk_level="low",
        risk_score=0.0,
        risk_explanation=reason,
        affected_by_depth={},
        risk_factors=[reason],
    )


def analyze(context: ContextResult, graph: GraphResult) -> ImpactResult:
    """
    Input:  ContextResult, GraphResult
    Output: ImpactResult
    """
    rid = context["request_id"]
    focus = graph.get("focus_node_id")

    if not focus:
        return _empty_impact(rid, "No focus node — impact analysis skipped (missing or empty graph).")

    direct = graph.get("direct_dependencies") or []
    indirect = graph.get("indirect_dependencies") or []
    upstream = graph.get("upstream_dependencies") or []
    propagation_depth = _propagation_depth_from_graph(graph)
    scope = _propagation_scope(focus, direct, indirect, upstream)

    affected_by_depth: dict[str, list[str]] = {"0": [focus], "1": direct}
    if indirect:
        affected_by_depth["2+"] = indirect
    if upstream:
        affected_by_depth["upstream"] = upstream

    affected_ids = {focus, *direct, *indirect, *upstream}
    cycles = graph.get("circular_dependencies") or []
    risk_factors = _collect_risk_flags(context, affected_ids)

    if cycles:
        risk_factors.append(f"{len(cycles)} circular dependency group(s) detected")
    if len(upstream) > 2:
        risk_factors.append(f"{len(upstream)} upstream modules may break from this change")

    risk_score, risk_level = _score_risk(
        propagation_depth,
        scope["total_affected"],
        len(cycles),
        len(risk_factors),
    )
    severity = _impact_severity(risk_score, propagation_depth, len(cycles))
    explanation = _risk_explanation(severity, scope, risk_factors, graph)

    return make_impact_result(
        request_id=rid,
        propagation_depth=propagation_depth,
        propagation_scope=scope,
        impact_severity=severity,
        risk_level=risk_level,
        risk_score=risk_score,
        risk_explanation=explanation,
        affected_by_depth=affected_by_depth,
        risk_factors=risk_factors or ["No additional risk flags from dependency metadata."],
        ai_reasoning={
            "enabled": False,
            "provider": None,
            "summary": None,
            "notes": "Hook for IBM watsonx reasoning agent or vector search enrichment.",
        },
    )
