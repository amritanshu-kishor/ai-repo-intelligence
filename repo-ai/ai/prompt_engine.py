"""
Stage 4: Prompt Builder — intelligent template routing and assembly.

Maps detected intents to specialized prompts without changing orchestration flow.
Compatible with HuggingFace, watsonx, and mock providers (text in / text out).
"""

from __future__ import annotations

import json
from typing import Any

from ai.contracts import ContextResult, IntentResult, PromptResult, make_prompt_result
from config import PROMPTS_DIR

# Intent (from intent_classifier) → (routing_key, template file)
INTENT_ROUTING: dict[str, tuple[str, str]] = {
    "impact": ("impact_analysis", "impact.txt"),
    "dependency": ("dependency_analysis", "dependency.txt"),
    "summary": ("summary", "summary.txt"),
    "general": ("repository_qa", "architecture.txt"),
    "graph": ("repository_qa", "architecture.txt"),
}

DEFAULT_TEMPLATE = "architecture.txt"
FALLBACK_TEMPLATE_BODY = """You are a repository intelligence assistant.

=== USER QUESTION ===
{{query}}

=== CONTEXT ===
{{repository_summaries}}

=== GRAPH ===
{{graph_reasoning}}

Respond with sections: Explanation, Affected Files, Dependency Impact, Risk Level, Recommendations.
"""


def _resolve_template(intent_name: str) -> tuple[str, str, str]:
    """
    Returns (routing_key, template_filename, template_text).
    Falls back to architecture.txt, then embedded minimal template.
    """
    routing_key, filename = INTENT_ROUTING.get(
        intent_name, ("repository_qa", DEFAULT_TEMPLATE)
    )
    path = PROMPTS_DIR / filename

    if path.is_file():
        return routing_key, filename, path.read_text(encoding="utf-8")

    # Fallback 1: default architecture template
    default_path = PROMPTS_DIR / DEFAULT_TEMPLATE
    if default_path.is_file():
        return routing_key, DEFAULT_TEMPLATE, default_path.read_text(encoding="utf-8")

    # Fallback 2: embedded minimal template (missing file safety)
    return routing_key, "fallback_inline.txt", FALLBACK_TEMPLATE_BODY


def _render(template: str, variables: dict[str, str]) -> str:
    out = template
    for key, value in variables.items():
        out = out.replace(f"{{{{{key}}}}}", value)
    return out


def _extract_impacted_files(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Merge graph-affected nodes into a de-duplicated impacted file list."""
    seen: set[str] = set()
    files: list[dict[str, Any]] = []

    for node in graph.get("affected_nodes", []):
        node_id = node.get("id")
        if node_id and node_id not in seen:
            seen.add(node_id)
            files.append({
                "id": node_id,
                "path": node.get("label", node_id),
                "relation": node.get("relation"),
                "type": node.get("type"),
            })

    return files


def _assemble_variables(intent: IntentResult, context: ContextResult) -> dict[str, str]:
    """
    Merge orchestration outputs into prompt placeholders.
    Sources: summaries, dependencies, graph reasoning, impact analysis, user query.
    
    ENHANCED: Works even when graph is empty - uses dependency data directly.
    """
    data = context.get("data", {})
    graph = context.get("graph_insights", {})
    impact = context.get("impact_insights", {})

    repository_summaries = data.get("summaries", [])
    dependency_data = data.get("dependencies", {})
    dependency_chains = graph.get("dependency_chains", [])
    
    # CRITICAL FIX: If graph is empty, build file list from dependencies
    affected_nodes = graph.get("affected_nodes", [])
    if not affected_nodes and dependency_data:
        # Build affected files from dependency data instead
        import logging
        logging.info("Graph empty - building file list from dependencies")
        
        affected_files_set = set()
        
        # Add files from internal dependencies
        for dep in dependency_data.get("internal", []):
            from_file = dep.get("from", "")
            to_file = dep.get("to", "")
            if from_file:
                affected_files_set.add(from_file)
            if to_file:
                affected_files_set.add(to_file)
        
        # Convert to affected_nodes format
        affected_nodes = [
            {
                "id": file_path,
                "label": file_path,
                "relation": "dependency",
                "type": "file"
            }
            for file_path in sorted(affected_files_set)
        ]
        
        logging.info(f"Built {len(affected_nodes)} files from dependencies")
    # Use affected_nodes we built (either from graph or dependencies)
    impacted_files = _extract_impacted_files(dict(graph) if graph else {"affected_nodes": affected_nodes})

    graph_reasoning = {
        "focus_node_id": graph.get("focus_node_id"),
        "focus_label": graph.get("focus_label"),
        "direct_dependencies": graph.get("direct_dependencies", []),
        "indirect_dependencies": graph.get("indirect_dependencies", []),
        "upstream_dependencies": graph.get("upstream_dependencies", []),
        "circular_dependencies": graph.get("circular_dependencies", []),
        "traversal_explain": graph.get("traversal_explain", []),
    }

    impact_analysis = {
        "propagation_depth": impact.get("propagation_depth"),
        "risk_level": impact.get("risk_level"),
        "risk_score": impact.get("risk_score"),
        "affected_by_depth": impact.get("affected_by_depth", {}),
        "risk_factors": impact.get("risk_factors", []),
    }

    # Legacy combined payloads (parser API / vector search / graph DB compatible)
    context_payload = {
        "repository_id": context.get("repository_id"),
        "intent": context.get("intent"),
        "routing": INTENT_ROUTING.get(intent.get("intent", "general"), ("repository_qa", DEFAULT_TEMPLATE))[0],
        "summaries": repository_summaries,
        "dependencies": dependency_data,
        "vector_hits": data.get("vector_hits", []),
        "impact": impact_analysis,
    }

    graph_payload = {**graph_reasoning, "impacted_files": impacted_files, "impact": impact_analysis}

    return {
        "query": intent.get("query", ""),
        "repository_summaries": json.dumps(repository_summaries, indent=2, default=str),
        "dependency_data": json.dumps(dependency_data, indent=2, default=str),
        "dependency_chains": json.dumps(dependency_chains, indent=2, default=str),
        "impacted_files": json.dumps(impacted_files, indent=2, default=str),
        "graph_reasoning": json.dumps(graph_reasoning, indent=2, default=str),
        "impact_analysis": json.dumps(impact_analysis, indent=2, default=str),
        # Backward-compatible placeholders for older templates
        "context": json.dumps(context_payload, indent=2, default=str),
        "graph_insights": json.dumps(graph_payload, indent=2, default=str),
    }


def build(intent: IntentResult, context: ContextResult) -> PromptResult:
    """
    Input:  IntentResult, ContextResult
    Output: PromptResult (specialized prompt for ai_provider)
    
    CRITICAL: Ensures graph reasoning and impact analysis are injected into prompts.
    """
    import sys
    
    rid = intent["request_id"]
    intent_name = intent.get("intent", "general")

    routing_key, template_id, template = _resolve_template(intent_name)
    variables = _assemble_variables(intent, context)
    text = _render(template, variables)

    # Debug verification: ensure graph context is present
    graph_insights = context.get("graph_insights", {})
    impact_insights = context.get("impact_insights", {})
    
    # Log graph reasoning injection status
    focus_node = graph_insights.get("focus_node_id")
    if focus_node:
        print(f"[DEBUG] Graph reasoning injected: focus={graph_insights.get('focus_label')} "
              f"depth={graph_insights.get('propagation_depth', 0)} "
              f"direct={len(graph_insights.get('direct_dependencies', []))} "
              f"indirect={len(graph_insights.get('indirect_dependencies', []))} "
              f"circular={len(graph_insights.get('circular_dependencies', []))}",
              file=sys.stderr)
    else:
        print(f"[WARN] Prompt built without graph reasoning (request_id={rid})", file=sys.stderr)
    
    # Log impact analysis injection status
    propagation = impact_insights.get("propagation_depth", 0)
    if propagation:
        print(f"[DEBUG] Impact analysis injected: depth={propagation} "
              f"severity={impact_insights.get('impact_severity')} "
              f"risk={impact_insights.get('risk_level')} "
              f"score={impact_insights.get('risk_score', 0.0)}",
              file=sys.stderr)
    else:
        print(f"[WARN] Prompt built without impact analysis (request_id={rid})", file=sys.stderr)
    
    # Log prompt assembly summary
    print(f"[DEBUG] Prompt assembled: template={template_id} intent={intent_name} length={len(text)} chars",
          file=sys.stderr)

    return make_prompt_result(
        request_id=rid,
        intent=intent_name,
        template_id=template_id,
        text=text,
    )


def get_routing_key(intent_name: str) -> str:
    """Expose routing key for tests/debug without changing contracts."""
    return INTENT_ROUTING.get(intent_name, ("repository_qa", DEFAULT_TEMPLATE))[0]
