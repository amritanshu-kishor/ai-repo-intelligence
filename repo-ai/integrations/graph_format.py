"""
Normalize Cytoscape graph payloads from parser-workflow for the frontend.
Fixes double-wrapped { data: { data: ... } } elements.
"""

from __future__ import annotations

from typing import Any


def _unwrap_data(item: dict[str, Any]) -> dict[str, Any]:
    """Return the inner Cytoscape data dict for a node or edge."""
    if not isinstance(item, dict):
        return {}

    if "data" in item:
        inner = item["data"]
        if isinstance(inner, dict) and "data" in inner and ("id" in inner["data"] or "source" in inner["data"]):
            return dict(inner["data"])
        if isinstance(inner, dict):
            return dict(inner)

    if "id" in item or "source" in item:
        return dict(item)

    return {}


def _basename(path: str) -> str:
    if not path:
        return ""
    return path.replace("\\", "/").split("/")[-1]


def enrich_node_data(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure every node has a visible label (filename) and tooltip (full path)."""
    out = dict(data)
    full = out.get("full_path") or out.get("id") or ""
    label = out.get("label") or _basename(str(full)) or str(out.get("id", "node"))
    out["label"] = label
    out["shortLabel"] = _basename(str(label)) or label
    if full:
        out["tooltip"] = str(full)
    node_type = out.get("node_type") or out.get("type") or "file"
    out["node_type"] = node_type
    return out


def enrich_edge_data(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    rel = out.get("relation") or out.get("relationship") or out.get("edge_type") or "imports"
    out["label"] = out.get("label") or rel
    out["relation"] = rel
    return out


def normalize_cytoscape_graph(graph_data: dict[str, Any]) -> dict[str, Any]:
    """
    Input: graph dict with nodes, edges, and/or elements from parser-workflow.
    Output: { nodes, edges, elements } with consistent Cytoscape.js shape.
    """
    raw_nodes = graph_data.get("nodes", [])
    raw_edges = graph_data.get("edges", [])
    raw_elements = graph_data.get("elements", [])

    node_elements: list[dict[str, Any]] = []
    edge_elements: list[dict[str, Any]] = []

    if raw_elements:
        for elem in raw_elements:
            if not isinstance(elem, dict):
                continue
            data = _unwrap_data(elem)
            classes = elem.get("classes", "")
            if "source" in data:
                edge_elements.append({"data": enrich_edge_data(data), "classes": classes or data.get("edge_type", "")})
            else:
                node_elements.append({"data": enrich_node_data(data), "classes": classes or data.get("node_type", "")})
    else:
        for item in raw_nodes:
            if isinstance(item, dict) and "data" in item and "source" not in item.get("data", {}):
                data = enrich_node_data(_unwrap_data(item))
                node_elements.append({"data": data, "classes": item.get("classes", data.get("node_type", ""))})
            else:
                data = enrich_node_data(_unwrap_data(item if isinstance(item, dict) else {}))
                if data.get("id"):
                    node_elements.append({"data": data, "classes": data.get("node_type", "")})

        for item in raw_edges:
            data = enrich_edge_data(_unwrap_data(item if isinstance(item, dict) else {}))
            if data.get("source") and data.get("target"):
                edge_elements.append({"data": data, "classes": data.get("edge_type", "")})

    elements = node_elements + edge_elements
    return {
        "nodes": node_elements,
        "edges": edge_elements,
        "elements": elements,
        "node_count": len(node_elements),
        "edge_count": len(edge_elements),
    }
