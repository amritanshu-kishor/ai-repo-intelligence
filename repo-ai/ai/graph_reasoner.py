"""
Phase 2: Graph reasoning over repository graph JSON.
Frontend-independent — outputs structured traversal data only.

Supports:
  - direct and indirect dependency paths
  - propagation depth
  - circular dependency detection
  - graph-aware reasoning summaries
  - future Neo4j / NetworkX / graph API replacement (see load_graph)
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from ai.contracts import ContextResult, GraphResult, make_graph_result
from config import GRAPH_API_URL, GRAPH_DB_URL


def load_graph(context: ContextResult) -> dict[str, Any]:
    """
    Graph DB / API replacement point.
    Today: graph slice from ContextResult.data.
    Future: fetch from Neo4j, NetworkX export, or GRAPH_API_URL / GRAPH_DB_URL.
    """
    raw = context.get("data", {}).get("graph") or {}
    if GRAPH_DB_URL or GRAPH_API_URL:
        pass  # Future: remote graph fetch by repository_id
    return _normalize_graph(raw)


def _normalize_graph(raw: dict[str, Any]) -> dict[str, Any]:
    if not raw:
        return {"nodes": [], "edges": [], "format": "empty"}
    return {
        "nodes": raw.get("nodes") or [],
        "edges": raw.get("edges") or [],
        "format": raw.get("format", "unknown"),
    }


def _adjacency(graph: dict[str, Any]) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = defaultdict(list)
    for edge in graph.get("edges", []):
        data = edge.get("data", edge)
        src, tgt = data.get("source"), data.get("target")
        if src and tgt:
            adj[src].append(tgt)
    return dict(adj)


def _reverse_adjacency(adj: dict[str, list[str]]) -> dict[str, list[str]]:
    rev: dict[str, list[str]] = defaultdict(list)
    for src, targets in adj.items():
        for tgt in targets:
            rev[tgt].append(src)
    return dict(rev)


def _node_index(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for node in graph.get("nodes", []):
        data = node.get("data", node)
        node_id = data.get("id")
        if node_id:
            index[node_id] = data
    return index


def _label(node_id: str, index: dict[str, dict[str, Any]]) -> str:
    return str(index.get(node_id, {}).get("label", node_id))


def _match_focus_node(query: str, index: dict[str, dict[str, Any]]) -> str | None:
    q = query.lower()
    for node_id, data in index.items():
        label = str(data.get("label", "")).lower()
        if node_id.lower() in q or (label and label in q):
            return node_id
    return None


def _default_focus_node(index: dict[str, dict[str, Any]]) -> str | None:
    for node_id, data in index.items():
        if data.get("type") == "entrypoint":
            return node_id
    return next(iter(index), None)


def _bfs_with_depth(
    adj: dict[str, list[str]],
    start: str,
    max_depth: int = 10,
) -> dict[str, int]:
    depths: dict[str, int] = {start: 0}
    queue: deque[tuple[str, int]] = deque([(start, 0)])
    while queue:
        node, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for nxt in adj.get(node, []):
            if nxt not in depths:
                depths[nxt] = depth + 1
                queue.append((nxt, depth + 1))
    return depths


def _build_paths(
    focus: str,
    depths: dict[str, int],
    adj: dict[str, list[str]],
    path_type: str,
) -> list[dict[str, Any]]:
    """Build explainable direct (depth 1) or indirect (depth > 1) paths from focus."""
    paths: list[dict[str, Any]] = []
    for node, depth in depths.items():
        if node == focus:
            continue
        if path_type == "direct" and depth != 1:
            continue
        if path_type == "indirect" and depth <= 1:
            continue
        paths.append({
            "from": focus,
            "to": node,
            "depth": depth,
            "type": path_type,
            "description": f"{focus} -> {node} (depth {depth})",
        })
    return paths


def _find_cycles(adj: dict[str, list[str]]) -> list[list[str]]:
    """Future: NetworkX simple_cycles or Neo4j cycle queries."""
    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: list[str] = []
    in_stack: set[str] = set()

    def dfs(node: str) -> None:
        visited.add(node)
        stack.append(node)
        in_stack.add(node)
        for nxt in adj.get(node, []):
            if nxt not in visited:
                dfs(nxt)
            elif nxt in in_stack:
                start_idx = stack.index(nxt)
                cycle = stack[start_idx:] + [nxt]
                if cycle not in cycles:
                    cycles.append(cycle)
        stack.pop()
        in_stack.discard(node)

    for node in adj:
        if node not in visited:
            dfs(node)
    return cycles


def _build_chains(focus: str, adj: dict[str, list[str]], max_chains: int = 5) -> list[list[str]]:
    chains: list[list[str]] = []

    def walk(path: list[str], depth: int) -> None:
        if len(chains) >= max_chains or depth > 6:
            return
        node = path[-1]
        children = adj.get(node, [])
        if not children:
            if len(path) > 1:
                chains.append(path.copy())
            return
        for child in children:
            if child in path:
                chains.append(path + [child])
                continue
            walk(path + [child], depth + 1)

    walk([focus], 0)
    return chains


def _build_traversal_explain(
    focus: str,
    index: dict[str, dict[str, Any]],
    direct: list[str],
    indirect: list[str],
    upstream: list[str],
    propagation_depth: int,
    cycles: list[list[str]],
    chains: list[list[str]],
) -> list[str]:
    """Human-readable lines for demos and debug panels."""
    lines = [
        f"Focus: {_label(focus, index)} (id={focus})",
        f"Propagation depth (downstream): {propagation_depth}",
        f"Direct dependencies ({len(direct)}): {', '.join(_label(n, index) for n in direct) or 'none'}",
        f"Indirect dependencies ({len(indirect)}): {', '.join(_label(n, index) for n in indirect) or 'none'}",
        f"Upstream dependents ({len(upstream)}): {', '.join(_label(n, index) for n in upstream) or 'none'}",
    ]
    if cycles:
        for i, cycle in enumerate(cycles[:3], 1):
            cycle_labels = " -> ".join(_label(n, index) for n in cycle)
            lines.append(f"Cycle {i}: {cycle_labels}")
    if chains:
        for i, chain in enumerate(chains[:3], 1):
            chain_labels = " -> ".join(_label(n, index) for n in chain)
            lines.append(f"Chain {i}: {chain_labels}")
    return lines


def _reasoning_summary(
    focus: str,
    index: dict[str, dict[str, Any]],
    direct: list[str],
    indirect: list[str],
    upstream: list[str],
    propagation_depth: int,
    cycles: list[list[str]],
) -> dict[str, Any]:
    return {
        "focus_node_id": focus,
        "focus_label": _label(focus, index),
        "propagation_depth": propagation_depth,
        "direct_count": len(direct),
        "indirect_count": len(indirect),
        "upstream_count": len(upstream),
        "has_cycles": bool(cycles),
        "narrative": (
            f"Change at {_label(focus, index)} may propagate to "
            f"{len(direct)} direct and {len(indirect)} indirect dependencies; "
            f"{len(upstream)} upstream modules may be affected."
        ),
    }


def _empty_graph_result(request_id: str, explain: list[str]) -> GraphResult:
    return make_graph_result(
        request_id=request_id,
        focus_node_id=None,
        focus_label=None,
        direct_dependencies=[],
        indirect_dependencies=[],
        upstream_dependencies=[],
        downstream_ids=[],
        propagation_depth=0,
        direct_paths=[],
        indirect_paths=[],
        reasoning_summary={"narrative": "Graph data unavailable."},
        affected_nodes=[],
        dependency_chains=[],
        circular_dependencies=[],
        traversal_explain=explain,
        cytoscape_elements={"nodes": [], "edges": []},
    )


def reason(context: ContextResult) -> GraphResult:
    """
    Input:  ContextResult (data.graph)
    Output: GraphResult for impact_analyzer, prompt_engine, response_processor
    
    This function operates on REAL uploaded repository graph data from context.
    """
    import logging
    
    rid = context["request_id"]
    query = context.get("query", "")
    repo_id = context.get("repository_id", "unknown")
    
    logging.info(f"Graph reasoning for repository: {repo_id}")
    
    graph = load_graph(context)

    if not graph.get("nodes"):
        logging.warning("No graph nodes available for traversal")
        return _empty_graph_result(rid, ["No graph nodes available for traversal."])

    logging.info(f"Graph loaded: {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges")

    index = _node_index(graph)
    adj = _adjacency(graph)
    rev = _reverse_adjacency(adj)
    focus = _match_focus_node(query, index) or _default_focus_node(index)

    if not focus:
        logging.warning("Could not resolve a focus node from query or graph")
        return _empty_graph_result(rid, ["Could not resolve a focus node from query or graph."])

    logging.info(f"Focus node: {focus} ({_label(focus, index)})")

    downstream_depths = _bfs_with_depth(adj, focus)
    upstream_depths = _bfs_with_depth(rev, focus)

    direct = [n for n, d in downstream_depths.items() if d == 1]
    indirect = [n for n, d in downstream_depths.items() if d > 1]
    upstream = [n for n, d in upstream_depths.items() if d >= 1]
    propagation_depth = max((d for n, d in downstream_depths.items() if n != focus), default=0)

    logging.info(f"Dependencies: {len(direct)} direct, {len(indirect)} indirect, {len(upstream)} upstream")
    logging.info(f"Propagation depth: {propagation_depth}")

    downstream_ids = direct + indirect
    affected_ids = list({focus, *downstream_ids, *upstream})
    cycles = _find_cycles(adj)
    chains = _build_chains(focus, adj)
    direct_paths = _build_paths(focus, downstream_depths, adj, "direct")
    indirect_paths = _build_paths(focus, downstream_depths, adj, "indirect")

    if cycles:
        logging.warning(f"Circular dependencies detected: {len(cycles)} cycles")

    explain = _build_traversal_explain(
        focus, index, direct, indirect, upstream, propagation_depth, cycles, chains
    )
    summary = _reasoning_summary(focus, index, direct, indirect, upstream, propagation_depth, cycles)

    nodes = [n for n in graph["nodes"] if n.get("data", n).get("id") in affected_ids]
    edges = [
        e for e in graph["edges"]
        if e.get("data", e).get("source") in affected_ids
        and e.get("data", e).get("target") in affected_ids
    ]

    affected_nodes = [
        {
            "id": nid,
            "label": _label(nid, index),
            "type": index.get(nid, {}).get("type"),
            "depth": downstream_depths.get(nid, upstream_depths.get(nid, 0)),
            "relation": (
                "focus" if nid == focus
                else "direct" if nid in direct
                else "indirect" if nid in indirect
                else "upstream"
            ),
        }
        for nid in affected_ids
    ]

    logging.info(f"Graph reasoning complete: {len(affected_nodes)} affected nodes, {len(chains)} chains")

    return make_graph_result(
        request_id=rid,
        focus_node_id=focus,
        focus_label=index.get(focus, {}).get("label"),
        direct_dependencies=direct,
        indirect_dependencies=indirect,
        upstream_dependencies=upstream,
        downstream_ids=downstream_ids,
        propagation_depth=propagation_depth,
        direct_paths=direct_paths,
        indirect_paths=indirect_paths,
        reasoning_summary=summary,
        affected_nodes=affected_nodes,
        dependency_chains=chains,
        circular_dependencies=cycles,
        traversal_explain=explain,
        cytoscape_elements={"nodes": nodes, "edges": edges},
    )
