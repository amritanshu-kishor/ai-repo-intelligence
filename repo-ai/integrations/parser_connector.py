"""
Parser Connector - Safe integration layer between repo-ai and parser-workflow.

This module provides:
- HTTP client for parser-workflow API endpoints
- Response normalization to repo-ai contracts
- Fallback handling for backend failures
- Graph structure validation
- Future-ready for Neo4j and ChromaDB integration

Integration Points:
- Parser API: http://127.0.0.1:8001/api/v1/parser/*
- Graph API: http://127.0.0.1:8001/api/v1/graph/cytoscape/*
- Repository API: http://127.0.0.1:8001/api/v1/repository/*

Future Integration Hooks:
- Neo4j: Graph database for production-scale dependency graphs
- ChromaDB: Vector search for semantic code search
- watsonx.ai: Enhanced AI reasoning over graph structures
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ParserConnectorError(Exception):
    """Base exception for parser connector errors."""
    pass


class ParserUnavailableError(ParserConnectorError):
    """Raised when parser-workflow backend is unavailable."""
    pass


class InvalidGraphDataError(ParserConnectorError):
    """Raised when graph data structure is invalid."""
    pass


class ParserConnector:
    """
    Safe connector to parser-workflow backend.
    
    Handles:
    - HTTP communication with retry logic
    - Response normalization
    - Error handling and fallback
    - Data validation
    """
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize parser connector.
        
        Args:
            base_url: Base URL of parser-workflow API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON data
            
        Raises:
            ParserUnavailableError: If backend is unreachable
            ParserConnectorError: For other errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Parser backend unavailable at {url}: {e}")
            raise ParserUnavailableError(
                f"Cannot connect to parser-workflow at {self.base_url}. "
                "Ensure the backend is running on port 8001."
            ) from e
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout for {url}: {e}")
            raise ParserUnavailableError(
                f"Parser backend timeout after {self.timeout}s"
            ) from e
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            status = e.response.status_code if e.response else "unknown"
            text = e.response.text if e.response else str(e)
            raise ParserConnectorError(
                f"Parser API error: {status} - {text}"
            ) from e
            
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise ParserConnectorError(f"Unexpected error: {e}") from e
    
    def fetch_repository_summaries(
        self,
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Fetch repository summaries from parser backend.
        
        Returns normalized format:
        {
            "repository_id": str,
            "items": [
                {
                    "path": str,
                    "summary": str,
                    "symbols": list[str]
                }
            ]
        }
        
        Future: May integrate with ChromaDB for semantic search
        """
        # TODO: Implement actual parser API endpoint for summaries
        # For now, this is a placeholder that will use the graph endpoint
        logger.warning(
            f"Repository summaries endpoint not yet implemented for {repository_id}. "
            "Using fallback mode."
        )
        raise ParserUnavailableError(
            "Summaries endpoint not yet implemented in parser-workflow"
        )
    
    def fetch_dependency_graph(
        self,
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Fetch dependency graph in Cytoscape format.
        
        Returns normalized format:
        {
            "repository_id": str,
            "format": "cytoscape-ready",
            "nodes": [{"data": {"id": str, "label": str, "type": str}}],
            "edges": [{"data": {"id": str, "source": str, "target": str, "relation": str}}]
        }
        
        Future: May integrate with Neo4j for production-scale graphs
        """
        try:
            endpoint = f"/api/v1/graph/cytoscape/{repository_id}"
            response = self._make_request("GET", endpoint)
            
            # Validate graph structure
            if "graph" not in response:
                raise InvalidGraphDataError(
                    "Response missing 'graph' field"
                )
            
            graph_data = response["graph"]
            
            # Handle both formats: elements array OR separate nodes/edges
            nodes = []
            edges = []
            
            if "nodes" in graph_data and "edges" in graph_data:
                # New format: separate nodes and edges arrays
                nodes = graph_data.get("nodes", [])
                edges = graph_data.get("edges", [])
            elif "elements" in graph_data:
                # Old format: elements array
                elements = graph_data.get("elements", [])
                for elem in elements:
                    if "source" in elem.get("data", {}):
                        edges.append(elem)
                    else:
                        nodes.append(elem)
            else:
                raise InvalidGraphDataError(
                    "Graph data missing both 'nodes'/'edges' and 'elements'"
                )
            
            from integrations.graph_format import normalize_cytoscape_graph

            graph_normalized = normalize_cytoscape_graph(
                {"nodes": nodes, "edges": edges, "elements": graph_data.get("elements", [])}
            )

            normalized = {
                "repository_id": repository_id,
                "format": "cytoscape-ready",
                **graph_normalized,
                "metrics": response.get("metrics", {}),
                "node_statistics": response.get("node_statistics", {}),
            }
            
            logger.info(
                f"✅ Fetched graph for {repository_id}: "
                f"{len(normalized['nodes'])} nodes, {len(normalized['edges'])} edges"
            )
            
            return normalized
            
        except (ParserUnavailableError, InvalidGraphDataError):
            raise
        except Exception as e:
            logger.error(f"Error fetching graph for {repository_id}: {e}")
            raise ParserConnectorError(f"Failed to fetch graph: {e}") from e
    
    def fetch_dependencies(
        self,
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Fetch dependency data (internal and external).
        
        Returns normalized format:
        {
            "repository_id": str,
            "external": [{"name": str, "version": str, "type": str}],
            "internal": [{"from": str, "to": str, "kind": str}],
            "risk_flags": [{"module": str, "issue": str, "severity": str}]
        }
        """
        try:
            endpoint = f"/api/v1/parser/dependencies/{repository_id}"
            response = self._make_request("GET", endpoint)
            
            # Normalize parser response to expected format
            dependencies = response.get("dependencies", [])
            
            # Group by type
            external = []
            internal = []
            
            for dep in dependencies:
                dep_type = dep.get("type", "")
                if dep_type in ["external", "package", "library"]:
                    external.append({
                        "name": dep.get("name", ""),
                        "version": dep.get("version", "unknown"),
                        "type": dep.get("details", "runtime"),
                    })
                elif dep_type in ["internal", "import", "module"]:
                    internal.append({
                        "from": dep.get("file_path", ""),
                        "to": dep.get("name", ""),
                        "kind": "import",
                    })
            
            normalized = {
                "repository_id": repository_id,
                "external": external,
                "internal": internal,
                "risk_flags": [],  # TODO: Add risk analysis
            }
            
            logger.info(
                f"Fetched dependencies for {repository_id}: "
                f"{len(external)} external, {len(internal)} internal"
            )
            
            return normalized
            
        except ParserUnavailableError:
            raise
        except Exception as e:
            logger.error(f"Error fetching dependencies for {repository_id}: {e}")
            raise ParserConnectorError(f"Failed to fetch dependencies: {e}") from e
    
    def fetch_all_context(
        self,
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Fetch all repository context in one call.
        
        Returns standardized format:
        {
            "repository_context": {
                "repository_id": str,
                "summaries": dict,
                "metadata": dict
            },
            "graph_data": dict,
            "dependencies": dict,
            "vector_results": list,
            "metadata": {
                "sources": list[str],
                "timestamp": str,
                "backend": str,
                "retrieval_mode": str
            }
        }
        
        This is the primary integration point for context_builder.py
        """
        import datetime
        
        context = {
            "repository_context": {
                "repository_id": repository_id,
                "summaries": None,
                "metadata": {},
            },
            "graph_data": None,
            "dependencies": None,
            "vector_results": [],
            "metadata": {
                "sources": [],
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "backend": "parser-workflow",
                "errors": [],
                "retrieval_mode": "live",
            },
        }
        
        # Fetch graph (critical for reasoning)
        try:
            graph = self.fetch_dependency_graph(repository_id)
            context["graph_data"] = graph
            context["metadata"]["sources"].append("graph_api")
            logger.info(f"✓ Graph data fetched: {len(graph.get('nodes', []))} nodes")
        except Exception as e:
            logger.error(f"✗ Failed to fetch graph: {e}")
            context["metadata"]["errors"].append(f"graph: {str(e)}")
            context["metadata"]["retrieval_mode"] = "fallback"
        
        # Fetch dependencies (important for analysis)
        try:
            deps = self.fetch_dependencies(repository_id)
            context["dependencies"] = deps
            context["metadata"]["sources"].append("dependencies_api")
            logger.info(f"✓ Dependencies fetched: {len(deps.get('external', []))} external, {len(deps.get('internal', []))} internal")
        except Exception as e:
            logger.warning(f"✗ Failed to fetch dependencies: {e}")
            context["metadata"]["errors"].append(f"dependencies: {str(e)}")
        
        # Summaries not yet implemented in parser-workflow
        # This is expected and not an error
        logger.info("ℹ Summaries endpoint not yet implemented (using fallback)")
        context["metadata"]["errors"].append(
            "summaries: Not yet implemented in parser-workflow (using fallback)"
        )
        
        # Log retrieval summary
        logger.info(
            f"Context retrieval complete for {repository_id}: "
            f"mode={context['metadata']['retrieval_mode']}, "
            f"sources={len(context['metadata']['sources'])}, "
            f"errors={len(context['metadata']['errors'])}"
        )
        
        return context
    
    def health_check(self) -> bool:
        """
        Check if parser-workflow backend is available.
        
        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            # Try to reach the API docs endpoint
            response = self.session.get(
                f"{self.base_url}/docs",
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False


def _default_parser_url() -> str:
    try:
        from config import PARSER_WORKFLOW_URL
        return PARSER_WORKFLOW_URL
    except ImportError:
        return "http://127.0.0.1:8001"


# Singleton instance
parser_connector = ParserConnector(base_url=_default_parser_url())


# Future integration hooks (commented for reference)
"""
# Neo4j Integration Hook
class Neo4jConnector:
    def __init__(self, uri: str, auth: tuple[str, str]):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(uri, auth=auth)
    
    def fetch_graph(self, repository_id: str) -> dict[str, Any]:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n)-[r]->(m) WHERE n.repository_id = $repo_id "
                "RETURN n, r, m LIMIT 1000",
                repo_id=repository_id
            )
            return self._normalize_to_cytoscape(result)

# ChromaDB Integration Hook
class ChromaDBConnector:
    def __init__(self, host: str, port: int):
        import chromadb
        self.client = chromadb.HttpClient(host=host, port=port)
    
    def vector_search(
        self,
        query: str,
        repository_id: str,
        top_k: int = 5
    ) -> list[dict[str, Any]]:
        collection = self.client.get_collection(f"repo_{repository_id}")
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        return self._normalize_results(results)
"""

# Made with Bob
