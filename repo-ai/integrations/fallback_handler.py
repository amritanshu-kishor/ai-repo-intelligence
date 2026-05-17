"""
Fallback Handler - Safe degradation for backend failures.

Provides graceful fallback strategies when parser-workflow backend
is unavailable or returns incomplete data.

Fallback Strategies:
1. Mock data fallback (for development/testing)
2. Partial data handling (use what's available)
3. Empty structure fallback (minimal valid response)
4. Error context preservation (for debugging)

Future Integration:
- Cached responses for offline operation
- Retry with exponential backoff
- Circuit breaker pattern
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FallbackHandler:
    """
    Handles graceful degradation when backend services fail.
    
    Strategies:
    - Use mock data when available
    - Return partial data if some endpoints succeed
    - Provide minimal valid structures as last resort
    - Preserve error context for debugging
    """
    
    def __init__(self, mock_data_dir: Path | None = None):
        """
        Initialize fallback handler.
        
        Args:
            mock_data_dir: Directory containing mock data files
        """
        self.mock_data_dir = mock_data_dir
        self._mock_cache: dict[str, Any] = {}
    
    def _load_mock_data(self, filename: str) -> dict[str, Any] | None:
        """
        Load mock data from file with caching.
        
        Args:
            filename: Name of mock data file
            
        Returns:
            Mock data dict or None if not available
        """
        if filename in self._mock_cache:
            return self._mock_cache[filename]
        
        if not self.mock_data_dir:
            return None
        
        try:
            file_path = self.mock_data_dir / filename
            if not file_path.exists():
                logger.warning(f"Mock data file not found: {file_path}")
                return None
            
            with file_path.open(encoding="utf-8") as f:
                data = json.load(f)
                self._mock_cache[filename] = data
                logger.info(f"Loaded mock data from {filename}")
                return data
                
        except Exception as e:
            logger.error(f"Failed to load mock data from {filename}: {e}")
            return None
    
    def get_fallback_summaries(
        self,
        repository_id: str,
        error: Exception | None = None,
    ) -> dict[str, Any]:
        """
        Get fallback summaries data.
        
        Strategy:
        1. Try mock data
        2. Return minimal valid structure
        
        Args:
            repository_id: Repository identifier
            error: Original error that triggered fallback
            
        Returns:
            Fallback summaries data
        """
        logger.warning(
            f"Using fallback summaries for {repository_id}"
            + (f": {error}" if error else "")
        )
        
        # Try mock data first
        mock_data = self._load_mock_data("summaries.json")
        if mock_data:
            # Update repository_id to match request
            mock_data["repository_id"] = repository_id
            return mock_data
        
        # Return minimal valid structure
        return {
            "repository_id": repository_id,
            "items": [],
            "metadata": {
                "fallback": True,
                "reason": str(error) if error else "Backend unavailable",
            },
        }
    
    def get_fallback_graph(
        self,
        repository_id: str,
        error: Exception | None = None,
    ) -> dict[str, Any]:
        """
        Get fallback graph data.
        
        Strategy:
        1. Try mock data
        2. Return minimal valid Cytoscape structure
        
        Args:
            repository_id: Repository identifier
            error: Original error that triggered fallback
            
        Returns:
            Fallback graph data in Cytoscape format
        """
        logger.warning(
            f"Using fallback graph for {repository_id}"
            + (f": {error}" if error else "")
        )
        
        # Try mock data first
        mock_data = self._load_mock_data("graph.json")
        if mock_data:
            # Update repository_id to match request
            mock_data["repository_id"] = repository_id
            return mock_data
        
        # Return minimal valid Cytoscape structure
        return {
            "repository_id": repository_id,
            "format": "cytoscape-ready",
            "nodes": [],
            "edges": [],
            "metrics": {
                "fallback": True,
                "reason": str(error) if error else "Backend unavailable",
            },
            "node_statistics": {},
        }
    
    def get_fallback_dependencies(
        self,
        repository_id: str,
        error: Exception | None = None,
    ) -> dict[str, Any]:
        """
        Get fallback dependencies data.
        
        Strategy:
        1. Try mock data
        2. Return minimal valid structure
        
        Args:
            repository_id: Repository identifier
            error: Original error that triggered fallback
            
        Returns:
            Fallback dependencies data
        """
        logger.warning(
            f"Using fallback dependencies for {repository_id}"
            + (f": {error}" if error else "")
        )
        
        # Try mock data first
        mock_data = self._load_mock_data("dependencies.json")
        if mock_data:
            # Update repository_id to match request
            mock_data["repository_id"] = repository_id
            return mock_data
        
        # Return minimal valid structure
        return {
            "repository_id": repository_id,
            "external": [],
            "internal": [],
            "risk_flags": [],
            "metadata": {
                "fallback": True,
                "reason": str(error) if error else "Backend unavailable",
            },
        }
    
    def handle_partial_failure(
        self,
        repository_id: str,
        available_data: dict[str, Any],
        failed_components: list[str],
    ) -> dict[str, Any]:
        """
        Handle partial backend failure by using available data.
        
        Strategy:
        - Use successfully fetched data
        - Fill missing components with fallbacks
        - Preserve error information
        
        Args:
            repository_id: Repository identifier
            available_data: Data that was successfully fetched
            failed_components: List of components that failed
            
        Returns:
            Complete context with fallbacks for missing data
        """
        logger.warning(
            f"Handling partial failure for {repository_id}. "
            f"Failed components: {', '.join(failed_components)}"
        )
        
        result = {
            "repository_context": available_data.get("repository_context", {}),
            "graph_data": available_data.get("graph_data"),
            "dependencies": available_data.get("dependencies"),
            "vector_results": available_data.get("vector_results", []),
            "metadata": {
                "sources": available_data.get("metadata", {}).get("sources", []),
                "timestamp": None,
                "backend": "parser-workflow",
                "errors": [],
                "partial_failure": True,
                "failed_components": failed_components,
            },
        }
        
        # Fill missing components with fallbacks
        if "summaries" in failed_components and not result["repository_context"]:
            result["repository_context"] = self.get_fallback_summaries(repository_id)
        
        if "graph" in failed_components and not result["graph_data"]:
            result["graph_data"] = self.get_fallback_graph(repository_id)
        
        if "dependencies" in failed_components and not result["dependencies"]:
            result["dependencies"] = self.get_fallback_dependencies(repository_id)
        
        return result
    
    def validate_and_repair_graph(
        self,
        graph_data: dict[str, Any],
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Validate graph data and repair if possible.
        
        Repairs:
        - Add missing required fields
        - Fix malformed node/edge structures
        - Ensure Cytoscape compatibility
        
        Args:
            graph_data: Graph data to validate
            repository_id: Repository identifier
            
        Returns:
            Validated and repaired graph data
        """
        if not isinstance(graph_data, dict):
            logger.error("Graph data is not a dict, using fallback")
            return self.get_fallback_graph(repository_id)
        
        # Ensure required fields exist
        if "nodes" not in graph_data:
            logger.warning("Graph missing 'nodes', adding empty list")
            graph_data["nodes"] = []
        
        if "edges" not in graph_data:
            logger.warning("Graph missing 'edges', adding empty list")
            graph_data["edges"] = []
        
        # Validate and repair nodes
        valid_nodes = []
        for node in graph_data.get("nodes", []):
            if not isinstance(node, dict) or "data" not in node:
                logger.warning(f"Skipping invalid node: {node}")
                continue
            
            node_data = node["data"]
            if "id" not in node_data:
                logger.warning(f"Node missing 'id': {node_data}")
                continue
            
            if "label" not in node_data:
                node_data["label"] = node_data["id"]
            
            valid_nodes.append(node)
        
        graph_data["nodes"] = valid_nodes
        
        # Validate and repair edges
        valid_edges = []
        node_ids = {n["data"]["id"] for n in valid_nodes}
        
        for edge in graph_data.get("edges", []):
            if not isinstance(edge, dict) or "data" not in edge:
                logger.warning(f"Skipping invalid edge: {edge}")
                continue
            
            edge_data = edge["data"]
            if "source" not in edge_data or "target" not in edge_data:
                logger.warning(f"Edge missing source/target: {edge_data}")
                continue
            
            # Skip edges referencing non-existent nodes
            if edge_data["source"] not in node_ids or edge_data["target"] not in node_ids:
                logger.warning(
                    f"Edge references non-existent nodes: "
                    f"{edge_data['source']} -> {edge_data['target']}"
                )
                continue
            
            if "id" not in edge_data:
                edge_data["id"] = f"{edge_data['source']}_to_{edge_data['target']}"
            
            valid_edges.append(edge)
        
        graph_data["edges"] = valid_edges
        
        # Ensure format field
        if "format" not in graph_data:
            graph_data["format"] = "cytoscape-ready"
        
        # Ensure repository_id
        if "repository_id" not in graph_data:
            graph_data["repository_id"] = repository_id
        
        logger.info(
            f"Validated graph: {len(valid_nodes)} nodes, {len(valid_edges)} edges"
        )
        
        return graph_data


# Singleton instance
_fallback_handler: FallbackHandler | None = None


def get_fallback_handler(mock_data_dir: Path | None = None) -> FallbackHandler:
    """
    Get or create fallback handler singleton.
    
    Args:
        mock_data_dir: Directory containing mock data files
        
    Returns:
        FallbackHandler instance
    """
    global _fallback_handler
    if _fallback_handler is None:
        _fallback_handler = FallbackHandler(mock_data_dir)
    return _fallback_handler


__all__ = [
    "FallbackHandler",
    "get_fallback_handler",
]

# Made with Bob
