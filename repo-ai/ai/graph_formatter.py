"""
Phase 2: Format graph data as Cytoscape-compatible JSON.
Frontend-independent — no rendering, layout, or UI logic.

Future Cytoscape enhancements: extend cytoscape_hints with layout/style presets
that the frontend team applies in Cytoscape.js.
"""

from __future__ import annotations

from typing import Any

from ai.contracts import (
    ContextResult,
    FormattedGraphResult,
    GraphResult,
    ImpactResult,
    make_formatted_graph_result,
)
from ai.graph_reasoner import load_graph


def _node_classes(node_id: str, graph: GraphResult, impact: ImpactResult) -> list[str]:
    classes = []
    if node_id == graph.get("focus_node_id"):
        classes.append("focus")
    if node_id in graph.get("direct_dependencies", []):
        classes.append("impacted-direct")
    if node_id in graph.get("indirect_dependencies", []):
        classes.append("impacted-indirect")
    if node_id in graph.get("upstream_dependencies", []):
        classes.append("impacted-upstream")
    risk = impact.get("risk_level", "low")
    if risk == "high" and classes:
        classes.append("high-risk")
    return classes or ["normal"]


def _edge_in_chain(edge_src: str, edge_tgt: str, chains: list[list[str]]) -> bool:
    for chain in chains:
        for i in range(len(chain) - 1):
            if chain[i] == edge_src and chain[i + 1] == edge_tgt:
                return True
    return False


def format_graph(
    context: ContextResult,
    graph: GraphResult,
    impact: ImpactResult,
) -> FormattedGraphResult:
    """
    Input:  ContextResult, GraphResult, ImpactResult
    Output: FormattedGraphResult — Cytoscape-ready elements + highlight metadata
    """
    rid = context["request_id"]
    raw = load_graph(context)
    chains = graph.get("dependency_chains", [])
    highlight_ids: list[str] = []
    chain_edge_ids: list[str] = []

    formatted_nodes: list[dict[str, Any]] = []
    for node in raw.get("nodes", []):
        data = dict(node.get("data", node))
        node_id = data.get("id")
        if not node_id:
            continue
        classes = _node_classes(node_id, graph, impact)
        data["classes"] = " ".join(classes)
        if "impacted" in " ".join(classes) or "focus" in classes:
            highlight_ids.append(node_id)
        formatted_nodes.append({"data": data})

    formatted_edges: list[dict[str, Any]] = []
    for edge in raw.get("edges", []):
        data = dict(edge.get("data", edge))
        src, tgt = data.get("source"), data.get("target")
        edge_id = data.get("id", f"{src}-{tgt}")
        if src and tgt and _edge_in_chain(src, tgt, chains):
            data["classes"] = "dependency-chain"
            chain_edge_ids.append(edge_id)
        elif src == graph.get("focus_node_id") or tgt in graph.get("direct_dependencies", []):
            data["classes"] = "impacted-edge"
        else:
            data["classes"] = "normal-edge"
        formatted_edges.append({"data": data})

    # Cytoscape hints: metadata only — frontend maps to stylesheet / layout plugins
    cytoscape_hints = {
        "layout_suggestion": "breadthfirst",
        "focus_node_id": graph.get("focus_node_id"),
        "class_legend": {
            "focus": "Change origin",
            "impacted-direct": "Direct dependency",
            "impacted-indirect": "Indirect dependency",
            "impacted-upstream": "Upstream dependent",
            "dependency-chain": "Highlighted dependency path",
            "high-risk": "Elevated risk from impact analyzer",
        },
        "future_enhancements": [
            "animated path tracing",
            "cluster compound nodes",
            "Neo4j live subgraph refresh",
        ],
    }

    return make_formatted_graph_result(
        request_id=rid,
        elements={"nodes": formatted_nodes, "edges": formatted_edges},
        highlight_node_ids=highlight_ids,
        chain_edge_ids=chain_edge_ids,
        cytoscape_hints=cytoscape_hints,
    )
