"""
Analytics Service for Repository Intelligence
Generates analytics data for Chart.js visualizations
"""
from typing import Any, Dict, List, Optional
import networkx as nx
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import random

from logger import get_logger

logger = get_logger()


class AnalyticsService:
    """Service for generating analytics and metrics for visualization"""
    
    def __init__(self):
        self.analytics_cache: Dict[str, Dict[str, Any]] = {}
    
    def generate_dependency_density(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Generate dependency density graph data
        Shows files vs dependency count
        """
        file_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "file"]
        
        dependency_counts = []
        labels = []
        
        for node in file_nodes:
            in_degree = G.in_degree(node)
            out_degree = G.out_degree(node)
            total_deps = in_degree + out_degree
            
            if total_deps > 0:  # Only include files with dependencies
                labels.append(G.nodes[node].get("label", node))
                dependency_counts.append(total_deps)
        
        # Sort by dependency count
        sorted_data = sorted(zip(labels, dependency_counts), key=lambda x: x[1], reverse=True)
        labels, dependency_counts = zip(*sorted_data[:20]) if sorted_data else ([], [])
        
        return {
            "type": "bar",
            "title": "Dependency Density (Top 20 Files)",
            "labels": list(labels),
            "datasets": [{
                "label": "Total Dependencies",
                "data": list(dependency_counts),
                "backgroundColor": "rgba(54, 162, 235, 0.6)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1
            }]
        }
    
    def generate_complexity_metrics(self, G: nx.DiGraph, parsed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate repository complexity metrics
        Shows imports, functions, classes, and LOC
        """
        file_data = {f.get("file"): f for f in parsed_files}
        
        metrics = {
            "imports": [],
            "functions": [],
            "classes": [],
            "loc": []
        }
        labels = []
        
        file_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "file"]
        
        for node in file_nodes[:15]:  # Top 15 files
            file_info = file_data.get(node, {})
            labels.append(G.nodes[node].get("label", node))
            metrics["imports"].append(len(file_info.get("imports", [])))
            metrics["functions"].append(len(file_info.get("functions", [])))
            metrics["classes"].append(len(file_info.get("classes", [])))
            metrics["loc"].append(file_info.get("loc", 0))
        
        return {
            "type": "bar",
            "title": "Repository Complexity Metrics",
            "labels": labels,
            "datasets": [
                {
                    "label": "Imports",
                    "data": metrics["imports"],
                    "backgroundColor": "rgba(255, 99, 132, 0.6)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "borderWidth": 1
                },
                {
                    "label": "Functions",
                    "data": metrics["functions"],
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1
                },
                {
                    "label": "Classes",
                    "data": metrics["classes"],
                    "backgroundColor": "rgba(255, 206, 86, 0.6)",
                    "borderColor": "rgba(255, 206, 86, 1)",
                    "borderWidth": 1
                },
                {
                    "label": "Lines of Code",
                    "data": metrics["loc"],
                    "backgroundColor": "rgba(75, 192, 192, 0.6)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "borderWidth": 1
                }
            ]
        }
    
    def generate_parsing_timeline(self, parsed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate parsing timeline showing files processed over time
        Simulates temporal data for demonstration
        """
        # Simulate timeline data
        num_files = len(parsed_files)
        time_points = 10
        files_per_point = max(1, num_files // time_points)
        
        labels = [f"T+{i}s" for i in range(time_points)]
        cumulative_files = [min((i + 1) * files_per_point, num_files) for i in range(time_points)]
        
        return {
            "type": "line",
            "title": "Parsing Timeline",
            "labels": labels,
            "datasets": [{
                "label": "Files Processed",
                "data": cumulative_files,
                "borderColor": "rgba(75, 192, 192, 1)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "fill": True,
                "tension": 0.4
            }]
        }
    
    def generate_language_distribution(self, parsed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate language distribution pie chart"""
        language_counts = Counter(f.get("language", "unknown") for f in parsed_files)
        
        colors = [
            "rgba(255, 99, 132, 0.8)",
            "rgba(54, 162, 235, 0.8)",
            "rgba(255, 206, 86, 0.8)",
            "rgba(75, 192, 192, 0.8)",
            "rgba(153, 102, 255, 0.8)",
            "rgba(255, 159, 64, 0.8)"
        ]
        
        return {
            "type": "pie",
            "title": "Language Distribution",
            "labels": list(language_counts.keys()),
            "datasets": [{
                "data": list(language_counts.values()),
                "backgroundColor": colors[:len(language_counts)],
                "borderColor": "rgba(255, 255, 255, 1)",
                "borderWidth": 2
            }]
        }
    
    def generate_function_call_heatmap(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Generate function call heatmap data
        Shows most connected functions/modules
        """
        function_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "function"]
        
        # Calculate connection scores
        connection_data = []
        for node in function_nodes[:20]:  # Top 20 functions
            in_degree = G.in_degree(node)
            out_degree = G.out_degree(node)
            connection_score = in_degree + out_degree
            
            if connection_score > 0:
                connection_data.append({
                    "label": G.nodes[node].get("label", node),
                    "score": connection_score,
                    "in": in_degree,
                    "out": out_degree
                })
        
        # Sort by score
        connection_data.sort(key=lambda x: x["score"], reverse=True)
        
        labels = [d["label"] for d in connection_data]
        scores = [d["score"] for d in connection_data]
        
        return {
            "type": "bar",
            "title": "Function Call Heatmap (Most Connected)",
            "labels": labels,
            "datasets": [{
                "label": "Connection Score",
                "data": scores,
                "backgroundColor": "rgba(255, 99, 132, 0.6)",
                "borderColor": "rgba(255, 99, 132, 1)",
                "borderWidth": 1
            }]
        }
    
    def generate_node_type_distribution(self, G: nx.DiGraph) -> Dict[str, Any]:
        """Generate distribution of node types in the graph"""
        node_types = Counter(d.get("node_type", "unknown") for _, d in G.nodes(data=True))
        
        colors = {
            "file": "rgba(54, 162, 235, 0.8)",
            "class": "rgba(255, 206, 86, 0.8)",
            "function": "rgba(75, 192, 192, 0.8)",
            "module": "rgba(153, 102, 255, 0.8)",
            "api": "rgba(255, 159, 64, 0.8)",
            "unknown": "rgba(201, 203, 207, 0.8)"
        }
        
        return {
            "type": "doughnut",
            "title": "Node Type Distribution",
            "labels": list(node_types.keys()),
            "datasets": [{
                "data": list(node_types.values()),
                "backgroundColor": [colors.get(k, "rgba(201, 203, 207, 0.8)") for k in node_types.keys()],
                "borderColor": "rgba(255, 255, 255, 1)",
                "borderWidth": 2
            }]
        }
    
    def generate_centrality_analysis(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Generate centrality analysis showing most important nodes
        """
        try:
            degree_centrality = nx.degree_centrality(G)
            
            # Get top 15 nodes by centrality
            top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:15]
            
            labels = [G.nodes[node].get("label", node) for node, _ in top_nodes]
            centrality_scores = [score * 100 for _, score in top_nodes]  # Convert to percentage
            
            return {
                "type": "horizontalBar",
                "title": "Node Centrality Analysis (Top 15)",
                "labels": labels,
                "datasets": [{
                    "label": "Centrality Score (%)",
                    "data": centrality_scores,
                    "backgroundColor": "rgba(153, 102, 255, 0.6)",
                    "borderColor": "rgba(153, 102, 255, 1)",
                    "borderWidth": 1
                }]
            }
        except Exception as e:
            logger.warning(f"Error generating centrality analysis: {e}")
            return {
                "type": "horizontalBar",
                "title": "Node Centrality Analysis",
                "labels": [],
                "datasets": []
            }
    
    def generate_graph_evolution(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Simulate graph evolution over time
        Shows how nodes and edges grew
        """
        total_nodes = G.number_of_nodes()
        total_edges = G.number_of_edges()
        
        # Simulate growth over 10 time periods
        time_points = 10
        labels = [f"Stage {i+1}" for i in range(time_points)]
        
        node_growth = [int((i + 1) * total_nodes / time_points) for i in range(time_points)]
        edge_growth = [int((i + 1) * total_edges / time_points) for i in range(time_points)]
        
        return {
            "type": "line",
            "title": "Repository Evolution",
            "labels": labels,
            "datasets": [
                {
                    "label": "Nodes",
                    "data": node_growth,
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "fill": False,
                    "tension": 0.4
                },
                {
                    "label": "Edges",
                    "data": edge_growth,
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "fill": False,
                    "tension": 0.4
                }
            ]
        }
    
    def generate_all_analytics(
        self, 
        G: nx.DiGraph, 
        parsed_files: List[Dict[str, Any]],
        repository_id: str
    ) -> Dict[str, Any]:
        """
        Generate all analytics charts for a repository
        
        Returns:
            Dictionary containing all chart data
        """
        analytics = {
            "repository_id": repository_id,
            "generated_at": datetime.utcnow().isoformat(),
            "charts": {
                "dependency_density": self.generate_dependency_density(G),
                "complexity_metrics": self.generate_complexity_metrics(G, parsed_files),
                "parsing_timeline": self.generate_parsing_timeline(parsed_files),
                "language_distribution": self.generate_language_distribution(parsed_files),
                "function_heatmap": self.generate_function_call_heatmap(G),
                "node_distribution": self.generate_node_type_distribution(G),
                "centrality_analysis": self.generate_centrality_analysis(G),
                "graph_evolution": self.generate_graph_evolution(G)
            },
            "summary": {
                "total_files": len([n for n, d in G.nodes(data=True) if d.get("node_type") == "file"]),
                "total_functions": len([n for n, d in G.nodes(data=True) if d.get("node_type") == "function"]),
                "total_classes": len([n for n, d in G.nodes(data=True) if d.get("node_type") == "class"]),
                "total_dependencies": G.number_of_edges(),
                "graph_density": round(nx.density(G), 4),
                "avg_degree": round(sum(dict(G.degree()).values()) / G.number_of_nodes(), 2) if G.number_of_nodes() > 0 else 0
            }
        }
        
        # Cache analytics
        self.analytics_cache[repository_id] = analytics
        
        return analytics
    
    def get_cached_analytics(self, repository_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analytics for a repository"""
        return self.analytics_cache.get(repository_id)


# Global service instance
analytics_service = AnalyticsService()

# Made with Bob
