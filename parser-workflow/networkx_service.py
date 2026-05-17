"""
NetworkX Graph Service for Repository Intelligence
Handles graph generation, analysis, traversal, and Cytoscape.js formatting
"""
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
from collections import defaultdict, deque
import json

from logger import get_logger

logger = get_logger()


class NetworkXGraphService:
    """Service for creating and analyzing repository dependency graphs using NetworkX"""

    def __init__(self):
        self.graphs: Dict[str, nx.DiGraph] = {}
        self._traversal_cache: Dict[str, Dict[str, Any]] = {}

    def create_graph_from_dependencies(
        self,
        repository_id: str,
        dependencies: List[Dict[str, Any]],
        parsed_files: List[Dict[str, Any]],
    ) -> nx.DiGraph:
        """
        Create a NetworkX directed graph from dependency data.
        Creates file, class, function, and external module nodes with real edges.
        """
        if repository_id in self.graphs:
            logger.info(f"Replacing existing graph for repository: {repository_id}")
        self._traversal_cache.pop(repository_id, None)

        G = nx.DiGraph()
        entry_candidates = {"main.py", "app.py", "index.js", "index.ts", "main.go", "Main.java"}

        # File nodes
        for file_data in parsed_files:
            file_path = file_data.get("file", "")
            if not file_path:
                continue

            filename = file_path.split("/")[-1]
            is_entry = filename in entry_candidates or filename.lower() in (
                "main.py", "app.py", "server.py", "manage.py"
            )

            node_attrs = {
                "label": filename,
                "full_path": file_path,
                "node_type": "file",
                "type": "entrypoint" if is_entry else "file",
                "language": file_data.get("language", "unknown"),
                "classes": len(file_data.get("classes", [])),
                "functions": len(file_data.get("functions", [])),
                "imports": len(file_data.get("imports", [])),
                "loc": file_data.get("loc", 0),
            }
            G.add_node(file_path, **node_attrs)

            for cls in file_data.get("classes", []):
                class_id = f"{file_path}::{cls['name']}"
                G.add_node(
                    class_id,
                    label=cls["name"],
                    node_type="class",
                    type="class",
                    parent_file=file_path,
                    methods=len(cls.get("methods", [])),
                )
                G.add_edge(file_path, class_id, edge_type="contains", relationship="contains")

            for func in file_data.get("functions", []):
                func_id = f"{file_path}::{func['name']}"
                G.add_node(
                    func_id,
                    label=func["name"],
                    node_type="function",
                    type="function",
                    parent_file=file_path,
                )
                G.add_edge(file_path, func_id, edge_type="contains", relationship="contains")

        # Ensure external / unresolved targets exist as nodes
        for dep in dependencies:
            target = dep.get("to", "")
            if not target:
                continue
            if not G.has_node(target):
                if dep.get("external") or str(target).startswith("ext:"):
                    G.add_node(
                        target,
                        label=str(target).replace("ext:", ""),
                        node_type="external",
                        type="external",
                        full_path="",
                        language="external",
                    )
                elif "::" in target:
                    G.add_node(target, label=target.split("::")[-1], node_type="class", type="class")
                else:
                    G.add_node(
                        target,
                        label=target.split("/")[-1],
                        node_type="module",
                        type="module",
                        full_path=target,
                    )

        edges_added = 0
        edges_skipped = 0

        for dep in dependencies:
            source = dep.get("from", "")
            target = dep.get("to", "")
            edge_type = dep.get("type", "imports")
            if not source or not target:
                edges_skipped += 1
                continue
            if not G.has_node(source):
                edges_skipped += 1
                continue
            if not G.has_node(target):
                G.add_node(
                    target,
                    label=str(target).split("/")[-1].replace("ext:", ""),
                    node_type="external" if dep.get("external") else "module",
                    type="external" if dep.get("external") else "module",
                )
            if not G.has_edge(source, target):
                G.add_edge(
                    source,
                    target,
                    edge_type=edge_type,
                    relationship=edge_type,
                    resolved=dep.get("resolved", True),
                )
                edges_added += 1

        self.graphs[repository_id] = G
        cycles = self.find_circular_dependencies(G)

        logger.info(
            f"Created graph for {repository_id}: "
            f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges "
            f"(added={edges_added}, skipped={edges_skipped}, cycles={len(cycles)})"
        )

        return G

    def get_graph(self, repository_id: str) -> Optional[nx.DiGraph]:
        return self.graphs.get(repository_id)

    def bfs_downstream(self, repository_id: str, start: str, max_depth: int = 10) -> Dict[str, int]:
        G = self.graphs.get(repository_id)
        if not G or not G.has_node(start):
            return {}
        depths: Dict[str, int] = {start: 0}
        queue: deque[Tuple[str, int]] = deque([(start, 0)])
        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for nxt in G.successors(node):
                if nxt not in depths:
                    depths[nxt] = depth + 1
                    queue.append((nxt, depth + 1))
        return depths

    def bfs_upstream(self, repository_id: str, start: str, max_depth: int = 10) -> Dict[str, int]:
        G = self.graphs.get(repository_id)
        if not G or not G.has_node(start):
            return {}
        depths: Dict[str, int] = {start: 0}
        queue: deque[Tuple[str, int]] = deque([(start, 0)])
        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for pred in G.predecessors(node):
                if pred not in depths:
                    depths[pred] = depth + 1
                    queue.append((pred, depth + 1))
        return depths

    def dfs_traverse(self, repository_id: str, start: str, direction: str = "downstream") -> List[str]:
        G = self.graphs.get(repository_id)
        if not G or not G.has_node(start):
            return []
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            order.append(node)
            neighbors = (
                list(G.successors(node))
                if direction == "downstream"
                else list(G.predecessors(node))
            )
            for nxt in neighbors:
                dfs(nxt)

        dfs(start)
        return order

    def get_propagation_depth(self, repository_id: str, start: str) -> int:
        depths = self.bfs_downstream(repository_id, start)
        if not depths:
            return 0
        return max((d for n, d in depths.items() if n != start), default=0)

    def calculate_metrics(self, G: nx.DiGraph) -> Dict[str, Any]:
        metrics = {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": nx.density(G) if G.number_of_nodes() > 1 else 0,
            "is_dag": nx.is_directed_acyclic_graph(G),
        }

        try:
            degree_centrality = nx.degree_centrality(G)
            metrics["avg_degree_centrality"] = (
                sum(degree_centrality.values()) / len(degree_centrality) if degree_centrality else 0
            )
            metrics["max_degree_centrality"] = max(degree_centrality.values()) if degree_centrality else 0
            top_central = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            metrics["top_central_nodes"] = [{"node": k, "centrality": v} for k, v in top_central]
        except Exception as e:
            logger.warning(f"Error calculating centrality: {e}")
            metrics["centrality_error"] = str(e)

        try:
            G_undirected = G.to_undirected()
            metrics["avg_clustering"] = nx.average_clustering(G_undirected)
        except Exception as e:
            logger.warning(f"Error calculating clustering: {e}")
            metrics["avg_clustering"] = 0

        try:
            scc = list(nx.strongly_connected_components(G))
            metrics["strongly_connected_components"] = len(scc)
            metrics["largest_scc_size"] = len(max(scc, key=len)) if scc else 0
        except Exception as e:
            logger.warning(f"Error calculating SCC: {e}")

        try:
            cycles = list(nx.simple_cycles(G))
            metrics["cycle_count"] = len(cycles)
            metrics["has_cycles"] = len(cycles) > 0
            metrics["cycles_sample"] = cycles[:5]
        except Exception as e:
            logger.warning(f"Error detecting cycles: {e}")
            metrics["cycle_count"] = 0
            metrics["has_cycles"] = False

        file_nodes = sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == "file")
        external_nodes = sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == "external")
        metrics["file_nodes"] = file_nodes
        metrics["external_nodes"] = external_nodes

        return metrics

    def to_cytoscape_format(self, G: nx.DiGraph) -> Dict[str, Any]:
        elements = []

        for node, attrs in G.nodes(data=True):
            node_type = attrs.get("node_type", "file")
            element = {
                "data": {
                    "id": node,
                    "label": attrs.get("label", node),
                    "node_type": node_type,
                    "type": attrs.get("type", node_type),
                    **{k: v for k, v in attrs.items() if k not in ("label",)},
                },
                "classes": node_type,
            }
            elements.append(element)

        for source, target, attrs in G.edges(data=True):
            edge_type = attrs.get("edge_type", "imports")
            relationship = attrs.get("relationship", edge_type)
            element = {
                "data": {
                    "id": f"{source}->{target}",
                    "source": source,
                    "target": target,
                    "edge_type": edge_type,
                    "relation": relationship,
                    "relationship": relationship,
                    **{k: v for k, v in attrs.items() if k not in ("edge_type", "relationship")},
                },
                "classes": edge_type,
            }
            elements.append(element)

        nodes = [e for e in elements if "source" not in e["data"]]
        edges = [e for e in elements if "source" in e["data"]]

        return {"elements": elements, "nodes": nodes, "edges": edges}

    def get_node_statistics(self, G: nx.DiGraph) -> Dict[str, Any]:
        stats = defaultdict(lambda: {"count": 0, "avg_degree": 0})

        for node, attrs in G.nodes(data=True):
            node_type = attrs.get("node_type", "unknown")
            stats[node_type]["count"] += 1
            stats[node_type]["avg_degree"] += G.degree(node)

        for node_type in stats:
            if stats[node_type]["count"] > 0:
                stats[node_type]["avg_degree"] /= stats[node_type]["count"]

        return dict(stats)

    def get_dependency_depth(self, G: nx.DiGraph, node: str) -> int:
        try:
            if not G.has_node(node):
                return 0
            depths = []
            for target in G.nodes():
                if target != node and nx.has_path(G, node, target):
                    try:
                        depths.append(nx.shortest_path_length(G, node, target))
                    except nx.NetworkXNoPath:
                        continue
            return max(depths) if depths else 0
        except Exception as e:
            logger.warning(f"Error calculating dependency depth: {e}")
            return 0

    def find_circular_dependencies(self, G: nx.DiGraph) -> List[List[str]]:
        try:
            return list(nx.simple_cycles(G))
        except Exception as e:
            logger.warning(f"Error finding cycles: {e}")
            return []

    def get_dependency_tree(self, G: nx.DiGraph, root_node: str, max_depth: int = 3) -> Dict[str, Any]:
        if not G.has_node(root_node):
            return {}

        def build_tree(node: str, depth: int) -> Dict[str, Any]:
            if depth >= max_depth:
                return {"id": node, "label": G.nodes[node].get("label", node), "children": []}
            children = []
            for successor in G.successors(node):
                children.append(build_tree(successor, depth + 1))
            return {
                "id": node,
                "label": G.nodes[node].get("label", node),
                "node_type": G.nodes[node].get("node_type", "unknown"),
                "children": children,
            }

        return build_tree(root_node, 0)

    def compare_graphs(self, repo_id_1: str, repo_id_2: str) -> Dict[str, Any]:
        G1 = self.graphs.get(repo_id_1)
        G2 = self.graphs.get(repo_id_2)

        if not G1 or not G2:
            return {"error": "One or both graphs not found"}

        comparison = {
            "repository_1": {
                "id": repo_id_1,
                "nodes": G1.number_of_nodes(),
                "edges": G1.number_of_edges(),
                "density": nx.density(G1),
            },
            "repository_2": {
                "id": repo_id_2,
                "nodes": G2.number_of_nodes(),
                "edges": G2.number_of_edges(),
                "density": nx.density(G2),
            },
            "differences": {
                "node_diff": G1.number_of_nodes() - G2.number_of_nodes(),
                "edge_diff": G1.number_of_edges() - G2.number_of_edges(),
                "density_diff": nx.density(G1) - nx.density(G2),
            },
        }

        common_nodes = set(G1.nodes()) & set(G2.nodes())
        comparison["common_nodes"] = len(common_nodes)
        comparison["unique_to_repo1"] = len(set(G1.nodes()) - set(G2.nodes()))
        comparison["unique_to_repo2"] = len(set(G2.nodes()) - set(G1.nodes()))

        return comparison

    async def generate_streaming_events(self, G: nx.DiGraph, delay: float = 0.1) -> List[Dict[str, Any]]:
        events = []

        for node, attrs in G.nodes(data=True):
            events.append({
                "type": "node",
                "data": {
                    "id": node,
                    "label": attrs.get("label", node),
                    "node_type": attrs.get("node_type", "file"),
                    **{k: v for k, v in attrs.items() if k not in ("label", "node_type")},
                },
            })
            await asyncio.sleep(delay)

        for source, target, attrs in G.edges(data=True):
            events.append({
                "type": "edge",
                "data": {
                    "source": source,
                    "target": target,
                    "edge_type": attrs.get("edge_type", "imports"),
                },
            })
            await asyncio.sleep(delay)

        events.append({
            "type": "complete",
            "data": {
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
            },
        })

        return events


networkx_service = NetworkXGraphService()
