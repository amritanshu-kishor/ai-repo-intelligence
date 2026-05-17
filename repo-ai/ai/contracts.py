"""
Shared JSON contracts between orchestration stages (Phase 1 + Phase 2).
Every module accepts the previous stage payload and returns a documented shape.
"""

from __future__ import annotations

import uuid
from typing import Any, TypedDict

SCHEMA_VERSION = "1.0"

# --- Stage names ---
STAGE_INTENT = "intent"
STAGE_CONTEXT = "context"
STAGE_GRAPH = "graph"
STAGE_IMPACT = "impact"
STAGE_FORMATTED_GRAPH = "formatted_graph"
STAGE_PROMPT = "prompt"
STAGE_LLM = "llm"
STAGE_RESPONSE = "response"
STAGE_VISUALIZATION = "visualization"


class IntentResult(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    query: str
    intent: str
    confidence: float
    scores: dict[str, float]


class GraphResult(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    focus_node_id: str | None
    focus_label: str | None
    direct_dependencies: list[str]
    indirect_dependencies: list[str]
    upstream_dependencies: list[str]
    downstream_ids: list[str]
    propagation_depth: int
    direct_paths: list[dict[str, Any]]
    indirect_paths: list[dict[str, Any]]
    reasoning_summary: dict[str, Any]
    affected_nodes: list[dict[str, Any]]
    dependency_chains: list[list[str]]
    circular_dependencies: list[list[str]]
    traversal_explain: list[str]
    cytoscape_elements: dict[str, Any]


class ImpactResult(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    propagation_depth: int
    propagation_scope: dict[str, Any]
    impact_severity: str
    risk_level: str
    risk_score: float
    risk_explanation: str
    affected_by_depth: dict[str, list[str]]
    risk_factors: list[str]
    ai_reasoning: dict[str, Any]


class StructuredIntelligence(TypedDict, total=False):
    """Normalized repository intelligence output for APIs and frontend."""
    summary: str
    affected_files: list[dict[str, Any]]
    dependency_chain: list[Any]
    risk_level: str
    recommendations: list[str]
    confidence_score: float
    graph_analysis: dict[str, Any]
    visualization_context: dict[str, Any]


class FormattedGraphResult(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    elements: dict[str, Any]
    highlight_node_ids: list[str]
    chain_edge_ids: list[str]
    cytoscape_hints: dict[str, Any]


class ContextResult(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    query: str
    intent: str
    repository_id: str
    data: dict[str, Any]
    graph_insights: GraphResult
    impact_insights: ImpactResult
    provenance: dict[str, Any]


class PromptResult(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    intent: str
    template_id: str
    text: str


class LLMResult(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    provider: str
    model: str
    text: str
    usage: dict[str, Any]


class PipelineResponse(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    query: str
    intent: str
    confidence: float
    answer: str
    highlights: list[str]
    intelligence: StructuredIntelligence
    graph: GraphResult
    impact: ImpactResult
    meta: dict[str, Any]
    provenance: dict[str, Any]
    visualization: VisualizationContext


class VisualizationContext(TypedDict, total=False):
    schema_version: str
    stage: str
    request_id: str
    repository_id: str
    query: str
    intent: str
    ai_explanation: dict[str, Any]
    graph_view: FormattedGraphResult
    impact_summary: ImpactResult
    exploration: dict[str, Any]
    debug: dict[str, Any]


def new_request_id() -> str:
    return str(uuid.uuid4())


def _base(stage: str, request_id: str) -> dict[str, str]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "request_id": request_id,
    }


def make_intent_result(
    *,
    request_id: str,
    query: str,
    intent: str,
    confidence: float,
    scores: dict[str, float] | None = None,
) -> IntentResult:
    result: IntentResult = {
        **_base(STAGE_INTENT, request_id),
        "query": query,
        "intent": intent,
        "confidence": confidence,
    }
    if scores is not None:
        result["scores"] = scores
    return result


def make_context_result(
    *,
    request_id: str,
    query: str,
    intent: str,
    repository_id: str,
    data: dict[str, Any],
    provenance: dict[str, Any],
    graph_insights: GraphResult | None = None,
    impact_insights: ImpactResult | None = None,
) -> ContextResult:
    result: ContextResult = {
        **_base(STAGE_CONTEXT, request_id),
        "query": query,
        "intent": intent,
        "repository_id": repository_id,
        "data": data,
        "provenance": provenance,
    }
    if graph_insights is not None:
        result["graph_insights"] = graph_insights
    if impact_insights is not None:
        result["impact_insights"] = impact_insights
    return result


def make_graph_result(
    *,
    request_id: str,
    focus_node_id: str | None,
    focus_label: str | None,
    direct_dependencies: list[str],
    indirect_dependencies: list[str],
    upstream_dependencies: list[str],
    downstream_ids: list[str],
    propagation_depth: int = 0,
    direct_paths: list[dict[str, Any]] | None = None,
    indirect_paths: list[dict[str, Any]] | None = None,
    reasoning_summary: dict[str, Any] | None = None,
    affected_nodes: list[dict[str, Any]],
    dependency_chains: list[list[str]],
    circular_dependencies: list[list[str]],
    traversal_explain: list[str],
    cytoscape_elements: dict[str, Any],
) -> GraphResult:
    return {
        **_base(STAGE_GRAPH, request_id),
        "focus_node_id": focus_node_id,
        "focus_label": focus_label,
        "direct_dependencies": direct_dependencies,
        "indirect_dependencies": indirect_dependencies,
        "upstream_dependencies": upstream_dependencies,
        "downstream_ids": downstream_ids,
        "propagation_depth": propagation_depth,
        "direct_paths": direct_paths or [],
        "indirect_paths": indirect_paths or [],
        "reasoning_summary": reasoning_summary or {},
        "affected_nodes": affected_nodes,
        "dependency_chains": dependency_chains,
        "circular_dependencies": circular_dependencies,
        "traversal_explain": traversal_explain,
        "cytoscape_elements": cytoscape_elements,
    }


def make_structured_intelligence(
    *,
    summary: str,
    affected_files: list[dict[str, Any]],
    dependency_chain: list[Any],
    risk_level: str,
    recommendations: list[str],
    confidence_score: float,
    graph_analysis: dict[str, Any],
    visualization_context: dict[str, Any] | None = None,
) -> StructuredIntelligence:
    return {
        "summary": summary,
        "affected_files": affected_files,
        "dependency_chain": dependency_chain,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "confidence_score": confidence_score,
        "graph_analysis": graph_analysis,
        "visualization_context": visualization_context or {},
    }


def make_impact_result(
    *,
    request_id: str,
    propagation_depth: int,
    propagation_scope: dict[str, Any],
    impact_severity: str,
    risk_level: str,
    risk_score: float,
    risk_explanation: str,
    affected_by_depth: dict[str, list[str]],
    risk_factors: list[str],
    ai_reasoning: dict[str, Any] | None = None,
) -> ImpactResult:
    return {
        **_base(STAGE_IMPACT, request_id),
        "propagation_depth": propagation_depth,
        "propagation_scope": propagation_scope,
        "impact_severity": impact_severity,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_explanation": risk_explanation,
        "affected_by_depth": affected_by_depth,
        "risk_factors": risk_factors,
        "ai_reasoning": ai_reasoning or {"enabled": False, "notes": "Future watsonx reasoning hook"},
    }


def make_formatted_graph_result(
    *,
    request_id: str,
    elements: dict[str, Any],
    highlight_node_ids: list[str],
    chain_edge_ids: list[str],
    cytoscape_hints: dict[str, Any],
) -> FormattedGraphResult:
    return {
        **_base(STAGE_FORMATTED_GRAPH, request_id),
        "elements": elements,
        "highlight_node_ids": highlight_node_ids,
        "chain_edge_ids": chain_edge_ids,
        "cytoscape_hints": cytoscape_hints,
    }


def make_prompt_result(
    *,
    request_id: str,
    intent: str,
    template_id: str,
    text: str,
) -> PromptResult:
    return {
        **_base(STAGE_PROMPT, request_id),
        "intent": intent,
        "template_id": template_id,
        "text": text,
    }


def make_llm_result(
    *,
    request_id: str,
    provider: str,
    model: str,
    text: str,
    usage: dict[str, Any] | None = None,
) -> LLMResult:
    return {
        **_base(STAGE_LLM, request_id),
        "provider": provider,
        "model": model,
        "text": text,
        "usage": usage or {},
    }


def make_pipeline_response(
    *,
    request_id: str,
    query: str,
    intent: str,
    confidence: float,
    answer: str,
    highlights: list[str],
    intelligence: StructuredIntelligence,
    graph: GraphResult,
    impact: ImpactResult,
    meta: dict[str, Any],
    provenance: dict[str, Any],
    visualization: VisualizationContext | None = None,
) -> PipelineResponse:
    result: PipelineResponse = {
        **_base(STAGE_RESPONSE, request_id),
        "query": query,
        "intent": intent,
        "confidence": confidence,
        "answer": answer,
        "highlights": highlights,
        "intelligence": intelligence,
        "graph": graph,
        "impact": impact,
        "meta": meta,
        "provenance": provenance,
    }
    if visualization is not None:
        result["visualization"] = visualization
    return result


def make_visualization_context(
    *,
    request_id: str,
    repository_id: str,
    query: str,
    intent: str,
    ai_explanation: dict[str, Any],
    graph_view: FormattedGraphResult,
    impact_summary: ImpactResult,
    exploration: dict[str, Any],
    debug: dict[str, Any],
) -> VisualizationContext:
    return {
        **_base(STAGE_VISUALIZATION, request_id),
        "repository_id": repository_id,
        "query": query,
        "intent": intent,
        "ai_explanation": ai_explanation,
        "graph_view": graph_view,
        "impact_summary": impact_summary,
        "exploration": exploration,
        "debug": debug,
    }
