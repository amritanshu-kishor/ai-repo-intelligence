"""
Standardized Response Format Contracts

Defines the expected data structures for integration between
parser-workflow and repo-ai systems.

These contracts ensure:
- Consistent data format across backends
- Easy validation and normalization
- Clear documentation for future integrations
- Type safety for Python 3.10+
"""

from __future__ import annotations

from typing import Any, TypedDict


class RepositoryContext(TypedDict, total=False):
    """
    Repository metadata and summary information.
    
    Source: parser-workflow summaries endpoint (future)
    """
    repository_id: str
    summaries: list[FileSummary]
    metadata: dict[str, Any]


class FileSummary(TypedDict, total=False):
    """Individual file summary from parser."""
    path: str
    summary: str
    symbols: list[str]
    language: str
    lines_of_code: int


class GraphNode(TypedDict, total=False):
    """Cytoscape-format graph node."""
    data: NodeData


class NodeData(TypedDict, total=False):
    """Node data structure."""
    id: str
    label: str
    type: str
    metadata: dict[str, Any]


class GraphEdge(TypedDict, total=False):
    """Cytoscape-format graph edge."""
    data: EdgeData


class EdgeData(TypedDict, total=False):
    """Edge data structure."""
    id: str
    source: str
    target: str
    relation: str
    metadata: dict[str, Any]


class GraphData(TypedDict, total=False):
    """
    Dependency graph in Cytoscape format.
    
    Source: parser-workflow /api/v1/graph/cytoscape/{repo_id}
    Future: May come from Neo4j graph database
    """
    repository_id: str
    format: str  # "cytoscape-ready"
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metrics: dict[str, Any]
    node_statistics: dict[str, Any]


class ExternalDependency(TypedDict, total=False):
    """External package dependency."""
    name: str
    version: str
    type: str  # "runtime" | "dev" | "peer"


class InternalDependency(TypedDict, total=False):
    """Internal module dependency."""
    from_: str  # Using from_ to avoid Python keyword
    to: str
    kind: str  # "import" | "require" | "include"


class RiskFlag(TypedDict, total=False):
    """Dependency risk indicator."""
    module: str
    issue: str
    severity: str  # "low" | "medium" | "high" | "critical"


class DependenciesData(TypedDict, total=False):
    """
    Dependency information (internal and external).
    
    Source: parser-workflow /api/v1/parser/dependencies/{repo_id}
    """
    repository_id: str
    external: list[ExternalDependency]
    internal: list[InternalDependency]
    risk_flags: list[RiskFlag]


class VectorSearchResult(TypedDict, total=False):
    """
    Vector search result for semantic code search.
    
    Future: ChromaDB integration
    """
    path: str
    content: str
    score: float
    metadata: dict[str, Any]


class IntegrationMetadata(TypedDict, total=False):
    """Metadata about data sources and integration status."""
    sources: list[str]
    timestamp: str | None
    backend: str
    errors: list[str]


class StandardizedResponse(TypedDict, total=False):
    """
    Standardized response format for all backend integrations.
    
    This is the primary contract between parser-workflow and repo-ai.
    All integration functions should return data in this format.
    """
    repository_context: RepositoryContext
    graph_data: GraphData | None
    dependencies: DependenciesData | None
    vector_results: list[VectorSearchResult]
    metadata: IntegrationMetadata


def validate_graph_data(data: dict[str, Any]) -> bool:
    """
    Validate graph data structure.
    
    Args:
        data: Graph data to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    # Check required fields
    if "nodes" not in data or "edges" not in data:
        return False
    
    # Validate nodes structure
    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        return False
    
    for node in nodes:
        if not isinstance(node, dict):
            return False
        if "data" not in node:
            return False
        node_data = node["data"]
        if "id" not in node_data or "label" not in node_data:
            return False
    
    # Validate edges structure
    edges = data.get("edges", [])
    if not isinstance(edges, list):
        return False
    
    for edge in edges:
        if not isinstance(edge, dict):
            return False
        if "data" not in edge:
            return False
        edge_data = edge["data"]
        if "source" not in edge_data or "target" not in edge_data:
            return False
    
    return True


def validate_dependencies_data(data: dict[str, Any]) -> bool:
    """
    Validate dependencies data structure.
    
    Args:
        data: Dependencies data to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    # Check for expected fields
    if "external" in data and not isinstance(data["external"], list):
        return False
    
    if "internal" in data and not isinstance(data["internal"], list):
        return False
    
    if "risk_flags" in data and not isinstance(data["risk_flags"], list):
        return False
    
    return True


def normalize_parser_response(
    raw_response: dict[str, Any],
    response_type: str,
) -> dict[str, Any]:
    """
    Normalize parser-workflow response to standardized format.
    
    Args:
        raw_response: Raw response from parser-workflow API
        response_type: Type of response ("graph" | "dependencies" | "summaries")
        
    Returns:
        Normalized response matching StandardizedResponse contract
    """
    if response_type == "graph":
        # Graph response is already in Cytoscape format
        return {
            "repository_id": raw_response.get("repository_id", ""),
            "format": "cytoscape-ready",
            "nodes": raw_response.get("nodes", []),
            "edges": raw_response.get("edges", []),
            "metrics": raw_response.get("metrics", {}),
            "node_statistics": raw_response.get("node_statistics", {}),
        }
    
    elif response_type == "dependencies":
        # Normalize dependencies response
        return {
            "repository_id": raw_response.get("repository_id", ""),
            "external": raw_response.get("external", []),
            "internal": raw_response.get("internal", []),
            "risk_flags": raw_response.get("risk_flags", []),
        }
    
    elif response_type == "summaries":
        # Normalize summaries response
        return {
            "repository_id": raw_response.get("repository_id", ""),
            "summaries": raw_response.get("items", raw_response.get("summaries", [])),
            "metadata": raw_response.get("metadata", {}),
        }
    
    return raw_response


# Export all contracts
__all__ = [
    "RepositoryContext",
    "FileSummary",
    "GraphData",
    "GraphNode",
    "GraphEdge",
    "NodeData",
    "EdgeData",
    "DependenciesData",
    "ExternalDependency",
    "InternalDependency",
    "RiskFlag",
    "VectorSearchResult",
    "IntegrationMetadata",
    "StandardizedResponse",
    "validate_graph_data",
    "validate_dependencies_data",
    "normalize_parser_response",
]

# Made with Bob
