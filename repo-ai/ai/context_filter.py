"""
Intelligent Context Filtering for Repository-Aware AI Reasoning

Transforms raw repository data into query-specific, focused context.
Prevents sending entire repository into prompts - retrieves ONLY relevant files.

Key Features:
- Query-based file relevance scoring
- Graph neighbor retrieval (upstream/downstream)
- Dependency chain extraction
- Impact zone identification
- Context size limiting
"""

from __future__ import annotations

import logging
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ContextFilter:
    """
    Intelligent context filtering for repository-aware reasoning.
    
    Retrieves ONLY relevant files based on:
    - Query keywords
    - Graph neighbors
    - Dependency chains
    - Impact zones
    """
    
    def __init__(self, max_files: int = 20, max_dependencies: int = 50):
        """
        Args:
            max_files: Maximum number of files to include in context
            max_dependencies: Maximum number of dependency edges to include
        """
        self.max_files = max_files
        self.max_dependencies = max_dependencies
    
    def filter_context(
        self,
        query: str,
        graph_data: dict[str, Any],
        dependency_data: dict[str, Any],
        focus_node: str | None = None,
    ) -> dict[str, Any]:
        """
        Filter repository context to ONLY relevant files and dependencies.
        
        Args:
            query: User's natural language query
            graph_data: Full graph with nodes and edges
            dependency_data: Full dependency data
            focus_node: Optional focus node from graph reasoning
            
        Returns:
            Filtered context with only relevant files and dependencies
        """
        logger.info(f"🔍 Filtering context for query: '{query[:50]}...'")
        
        # Extract query keywords
        keywords = self._extract_keywords(query)
        logger.info(f"   Keywords: {keywords}")
        
        # Score all nodes by relevance
        nodes = graph_data.get("nodes", [])
        scored_nodes = self._score_nodes(nodes, keywords, focus_node)
        
        # Get top relevant files
        relevant_files = scored_nodes[:self.max_files]
        relevant_ids = {node["id"] for node in relevant_files}
        
        logger.info(f"   Selected {len(relevant_files)} relevant files from {len(nodes)} total")
        
        # Filter edges to only those connecting relevant nodes
        edges = graph_data.get("edges", [])
        relevant_edges = self._filter_edges(edges, relevant_ids)
        
        logger.info(f"   Selected {len(relevant_edges)} relevant edges from {len(edges)} total")
        
        # Filter dependencies
        filtered_deps = self._filter_dependencies(
            dependency_data,
            relevant_ids,
            self.max_dependencies
        )
        
        # Build filtered context
        filtered_context = {
            "nodes": relevant_files,
            "edges": relevant_edges,
            "dependencies": filtered_deps,
            "focus_files": [node["id"] for node in relevant_files[:5]],
            "context_stats": {
                "total_files": len(nodes),
                "selected_files": len(relevant_files),
                "total_edges": len(edges),
                "selected_edges": len(relevant_edges),
                "keywords_matched": len(keywords),
                "focus_node": focus_node,
            }
        }
        
        logger.info(f"✅ Context filtered: {len(relevant_files)} files, {len(relevant_edges)} edges")
        
        return filtered_context
    
    def _extract_keywords(self, query: str) -> list[str]:
        """Extract meaningful keywords from query."""
        # Remove common words
        stop_words = {
            "what", "how", "why", "when", "where", "who", "which", "the", "a", "an",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "should", "could", "may", "might",
            "can", "if", "then", "else", "for", "to", "of", "in", "on", "at", "by",
            "with", "from", "about", "into", "through", "during", "before", "after",
            "show", "tell", "explain", "describe", "list", "find", "get", "give",
        }
        
        # Extract words
        words = query.lower().split()
        keywords = [
            word.strip(".,!?;:()[]{}\"'")
            for word in words
            if len(word) > 2 and word.lower() not in stop_words
        ]
        
        return keywords
    
    def _score_nodes(
        self,
        nodes: list[dict[str, Any]],
        keywords: list[str],
        focus_node: str | None,
    ) -> list[dict[str, Any]]:
        """
        Score nodes by relevance to query.
        
        Scoring factors:
        - Keyword match in node ID or label (high weight)
        - Focus node (highest weight)
        - Node type (files > classes > functions)
        """
        scored = []
        
        for node in nodes:
            data = node.get("data", node)
            node_id = data.get("id", "")
            label = data.get("label", "")
            node_type = data.get("node_type", "file")
            
            score = 0.0
            
            # Focus node gets highest score
            if focus_node and node_id == focus_node:
                score += 100.0
            
            # Keyword matches
            node_text = f"{node_id} {label}".lower()
            for keyword in keywords:
                if keyword in node_text:
                    score += 10.0
                    # Exact match gets bonus
                    if keyword == node_id.lower() or keyword == label.lower():
                        score += 20.0
            
            # Node type preference (files are most important)
            if node_type == "file":
                score += 5.0
            elif node_type == "class":
                score += 3.0
            elif node_type == "function":
                score += 1.0
            
            # Add to scored list
            scored.append({
                **data,
                "relevance_score": score,
            })
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return scored
    
    def _filter_edges(
        self,
        edges: list[dict[str, Any]],
        relevant_ids: set[str],
    ) -> list[dict[str, Any]]:
        """Filter edges to only those connecting relevant nodes."""
        filtered = []
        
        for edge in edges:
            data = edge.get("data", edge)
            source = data.get("source")
            target = data.get("target")
            
            # Keep edge if both source and target are relevant
            if source in relevant_ids and target in relevant_ids:
                filtered.append(edge)
        
        return filtered
    
    def _filter_dependencies(
        self,
        dependency_data: dict[str, Any],
        relevant_ids: set[str],
        max_deps: int,
    ) -> dict[str, Any]:
        """Filter dependencies to only those involving relevant files."""
        internal = dependency_data.get("internal", [])
        external = dependency_data.get("external", [])
        
        # Filter internal dependencies
        filtered_internal = [
            dep for dep in internal
            if dep.get("from") in relevant_ids or dep.get("to") in relevant_ids
        ][:max_deps]
        
        # Keep all external dependencies (usually not many)
        filtered_external = external[:max_deps]
        
        return {
            "internal": filtered_internal,
            "external": filtered_external,
            "risk_flags": dependency_data.get("risk_flags", []),
        }
    
    def get_graph_neighbors(
        self,
        node_id: str,
        graph_data: dict[str, Any],
        depth: int = 2,
    ) -> set[str]:
        """
        Get all graph neighbors within specified depth.
        
        Args:
            node_id: Starting node
            graph_data: Full graph data
            depth: How many hops to traverse
            
        Returns:
            Set of neighbor node IDs
        """
        edges = graph_data.get("edges", [])
        
        # Build adjacency lists
        forward = defaultdict(list)  # node -> dependencies
        backward = defaultdict(list)  # node -> dependents
        
        for edge in edges:
            data = edge.get("data", edge)
            source = data.get("source")
            target = data.get("target")
            if source and target:
                forward[source].append(target)
                backward[target].append(source)
        
        # BFS to find neighbors
        neighbors = {node_id}
        current_level = {node_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                # Add downstream dependencies
                next_level.update(forward.get(node, []))
                # Add upstream dependents
                next_level.update(backward.get(node, []))
            
            neighbors.update(next_level)
            current_level = next_level
            
            if not current_level:
                break
        
        return neighbors
    
    def get_dependency_chain(
        self,
        start_file: str,
        end_file: str,
        dependency_data: dict[str, Any],
        max_length: int = 10,
    ) -> list[list[str]]:
        """
        Find dependency chains between two files.
        
        Args:
            start_file: Starting file
            end_file: Target file
            dependency_data: Dependency data
            max_length: Maximum chain length
            
        Returns:
            List of dependency chains (each chain is a list of file paths)
        """
        internal = dependency_data.get("internal", [])
        
        # Build adjacency
        adj = defaultdict(list)
        for dep in internal:
            from_file = dep.get("from")
            to_file = dep.get("to")
            if from_file and to_file:
                adj[from_file].append(to_file)
        
        # BFS to find paths
        chains = []
        queue = [(start_file, [start_file])]
        visited = {start_file}
        
        while queue and len(chains) < 5:  # Limit to 5 chains
            current, path = queue.pop(0)
            
            if len(path) > max_length:
                continue
            
            if current == end_file:
                chains.append(path)
                continue
            
            for next_file in adj.get(current, []):
                if next_file not in visited:
                    visited.add(next_file)
                    queue.append((next_file, path + [next_file]))
        
        return chains


# Singleton instance
_context_filter = ContextFilter()


def filter_context(
    query: str,
    graph_data: dict[str, Any],
    dependency_data: dict[str, Any],
    focus_node: str | None = None,
) -> dict[str, Any]:
    """
    Filter repository context to only relevant files and dependencies.
    
    This is the main entry point for context filtering.
    """
    return _context_filter.filter_context(
        query=query,
        graph_data=graph_data,
        dependency_data=dependency_data,
        focus_node=focus_node,
    )


def get_graph_neighbors(
    node_id: str,
    graph_data: dict[str, Any],
    depth: int = 2,
) -> set[str]:
    """Get all graph neighbors within specified depth."""
    return _context_filter.get_graph_neighbors(node_id, graph_data, depth)


def get_dependency_chain(
    start_file: str,
    end_file: str,
    dependency_data: dict[str, Any],
    max_length: int = 10,
) -> list[list[str]]:
    """Find dependency chains between two files."""
    return _context_filter.get_dependency_chain(
        start_file, end_file, dependency_data, max_length
    )

# Made with Bob
