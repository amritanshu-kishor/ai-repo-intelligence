"""
Phase 2: Unified visualization + intelligence payload for frontend workflows.
Merges AI explanations, graph traversal, impact analysis, and Cytoscape data.
No rendering logic — structured JSON only.
"""

from __future__ import annotations

from typing import Any

from ai.contracts import (
    ContextResult,
    FormattedGraphResult,
    GraphResult,
    ImpactResult,
    IntentResult,
    PipelineResponse,
    StructuredIntelligence,
    VisualizationContext,
    make_visualization_context,
)
from ai.graph_formatter import format_graph


def _safe_format_graph(
    context: ContextResult,
    graph: GraphResult,
    impact: ImpactResult,
) -> FormattedGraphResult:
    """Defensive wrapper — empty graph if formatter fails."""
    try:
        return format_graph(context, graph, impact)
    except Exception as exc:  # noqa: BLE001 — hackathon-safe fallback
        rid = context.get("request_id", "")
        return {
            "schema_version": "1.0",
            "stage": "formatted_graph",
            "request_id": rid,
            "elements": graph.get("cytoscape_elements", {"nodes": [], "edges": []}),
            "highlight_node_ids": [],
            "chain_edge_ids": [],
            "cytoscape_hints": {"error": str(exc), "layout_suggestion": "breadthfirst"},
        }


def _build_frontend_intelligence(
    pipeline: PipelineResponse,
    graph: GraphResult,
    impact: ImpactResult,
    formatted: FormattedGraphResult,
    viz: VisualizationContext,
) -> dict[str, Any]:
    """
    Single frontend-ready intelligence object (includes required structured fields).
    Future Cytoscape enhancements: consume graph_view.elements + cytoscape_hints.
    """
    base: StructuredIntelligence = pipeline.get("intelligence") or {
        "summary": "",
        "affected_files": [],
        "dependency_chain": [],
        "risk_level": "low",
        "recommendations": [],
        "confidence_score": 0.0,
        "graph_analysis": {},
        "visualization_context": {},
    }

    return {
        "summary": base.get("summary", ""),
        "affected_files": base.get("affected_files", []),
        "dependency_chain": base.get("dependency_chain", []),
        "risk_level": base.get("risk_level", impact.get("risk_level", "low")),
        "recommendations": base.get("recommendations", []),
        "confidence_score": base.get("confidence_score", 0.0),
        "graph_analysis": base.get("graph_analysis", {}),
        "visualization_context": {
            "repository_id": viz.get("repository_id"),
            "query": viz.get("query"),
            "intent": viz.get("intent"),
            "ai_explanation": viz.get("ai_explanation", {}),
            "graph_traversal": {
                "focus_node_id": graph.get("focus_node_id"),
                "propagation_depth": graph.get("propagation_depth"),
                "traversal_explain": graph.get("traversal_explain", []),
                "dependency_chains": graph.get("dependency_chains", []),
            },
            "impact_analysis": {
                "impact_severity": impact.get("impact_severity"),
                "propagation_scope": impact.get("propagation_scope", {}),
                "risk_explanation": impact.get("risk_explanation"),
                "risk_factors": impact.get("risk_factors", []),
            },
            "cytoscape": {
                "elements": formatted.get("elements", {}),
                "highlight_node_ids": formatted.get("highlight_node_ids", []),
                "chain_edge_ids": formatted.get("chain_edge_ids", []),
                "hints": formatted.get("cytoscape_hints", {}),
            },
            "exploration": viz.get("exploration", {}),
            "debug": viz.get("debug", {}),
        },
    }


def build(
    intent: IntentResult,
    context: ContextResult,
    pipeline: PipelineResponse,
    *,
    graph: GraphResult | None = None,
    impact: ImpactResult | None = None,
    formatted_graph: FormattedGraphResult | None = None,
) -> VisualizationContext:
    """
    Merge orchestration + graph + impact into VisualizationContext.
    Also enriches pipeline.intelligence.visualization_context when present.
    """
    rid = intent["request_id"]
    graph = graph or context.get("graph_insights") or pipeline.get("graph") or {}
    impact = impact or context.get("impact_insights") or pipeline.get("impact") or {}
    formatted = formatted_graph or _safe_format_graph(context, graph, impact)

    intelligence_block = pipeline.get("intelligence") or {}
    ai_explanation = {
        "answer": pipeline.get("answer", ""),
        "summary": intelligence_block.get("summary", ""),
        "highlights": pipeline.get("highlights", []),
        "recommendations": intelligence_block.get("recommendations", []),
        "intent": pipeline.get("intent"),
        "confidence": pipeline.get("confidence"),
        "confidence_score": intelligence_block.get("confidence_score", 0.0),
        "provider": pipeline.get("meta", {}).get("provider"),
    }

    exploration: dict[str, Any] = {
        "highlighted_node_ids": formatted.get("highlight_node_ids", []),
        "dependency_chains": graph.get("dependency_chains", []),
        "chain_edge_ids": formatted.get("chain_edge_ids", []),
        "suggested_focus_nodes": [
            n.get("id") for n in (graph.get("affected_nodes") or [])[:5] if isinstance(n, dict)
        ],
        "interactive_hints": {
            "click_node": "Show module summary and upstream/downstream list",
            "hover_edge": "Show relation type from edge data",
            "filter_by_risk": impact.get("risk_level", "low"),
            "filter_by_severity": impact.get("impact_severity", "low"),
        },
    }

    debug = {
        "traversal_explain": graph.get("traversal_explain", []),
        "reasoning_summary": graph.get("reasoning_summary", {}),
        "risk_factors": impact.get("risk_factors", []),
        "provenance": context.get("provenance", {}),
    }

    viz = make_visualization_context(
        request_id=rid,
        repository_id=context.get("repository_id", ""),
        query=intent.get("query", ""),
        intent=intent.get("intent", "general"),
        ai_explanation=ai_explanation,
        graph_view=formatted,
        impact_summary=impact,
        exploration=exploration,
        debug=debug,
    )

    # Attach unified frontend intelligence to pipeline contract
    frontend_payload = _build_frontend_intelligence(pipeline, graph, impact, formatted, viz)
    if pipeline.get("intelligence") is not None:
        pipeline["intelligence"]["visualization_context"] = frontend_payload["visualization_context"]

    return viz
