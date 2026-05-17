"""Bridge to the empty-window Dependency Intelligence Engine (NetworkX)."""

from __future__ import annotations

import sys
import uuid
import logging
from pathlib import Path
from typing import Any, Dict, List, TYPE_CHECKING

from config import EMPTY_WINDOW_ENGINE_ROOT

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.graph.engine import DependencyIntelligenceEngine

# REMOVED: Static SAMPLE_GRAPH - all graphs must come from real repository uploads
# This ensures the system operates entirely on uploaded repository data


def _ensure_engine_on_path() -> Path | None:
    """Try to add engine to path, return None if not available (fallback mode)."""
    if not EMPTY_WINDOW_ENGINE_ROOT or EMPTY_WINDOW_ENGINE_ROOT == "":
        return None
    
    root = Path(EMPTY_WINDOW_ENGINE_ROOT).resolve()
    
    if not root.is_dir():
        return None
    
    root_str = str(root)
    
    # Remove any existing occurrence to avoid duplicates
    while root_str in sys.path:
        sys.path.remove(root_str)
    
    # Insert at the very beginning to ensure priority over other backend packages
    sys.path.insert(0, root_str)
    
    return root


def _import_engine_class():
    """Try to import engine class, return None if not available (fallback mode)."""
    engine_path = _ensure_engine_on_path()
    if engine_path is None:
        return None
    
    try:
        from backend.graph.engine import DependencyIntelligenceEngine
        return DependencyIntelligenceEngine
    except ImportError:
        return None


def module_from_file_path(file_path: str) -> str:
    """Map a repository file path to a graph module id (node id)."""
    return Path(file_path).stem


class EmptyWindowEngineRegistry:
    """In-memory engines keyed by repository_id - stores real uploaded repository graphs."""

    def __init__(self) -> None:
        self._engines: Dict[str, Any] = {}
        self._impact_requests: Dict[str, Dict[str, Any]] = {}
        self._affected_by_repository: Dict[str, List[Dict[str, str]]] = {}
        logger.info("🔧 EmptyWindowEngineRegistry initialized - ready for real repository graphs")

    def check_connection(self) -> str:
        engine_cls = _import_engine_class()
        if engine_cls is None:
            return "fallback_mode"
        return "available"

    def register_graph(self, repository_id: str, graph_data: dict[str, Any]) -> None:
        """Register a real repository graph - INVALIDATES any previous graph for this repository_id"""
        # CRITICAL: This invalidates previous graph for the same repository_id
        if repository_id in self._engines:
            logger.warning(f"⚠️  Overwriting existing graph for repository: {repository_id}")
        
        node_count = len(graph_data.get("nodes", []))
        edge_count = len(graph_data.get("edges", []))
        
        engine_cls = _import_engine_class()
        if engine_cls is None:
            # Fallback: store graph data directly without engine
            self._engines[repository_id] = {"graph_data": graph_data, "fallback": True}
            logger.info(f"✅ Registered graph for {repository_id} (fallback mode): {node_count} nodes, {edge_count} edges")
            return
        
        self._engines[repository_id] = engine_cls.from_json(graph_data)
        logger.info(f"✅ Registered graph for {repository_id} (engine mode): {node_count} nodes, {edge_count} edges")

    def get_engine(self, repository_id: str) -> Any:
        """Get engine or fallback data for repository."""
        if repository_id not in self._engines:
            # NO FALLBACK: Return empty graph structure if repository not registered
            # This forces the system to work only with real uploaded repositories
            logger.warning(f"⚠️  Repository '{repository_id}' not found in registry - returning empty graph")
            logger.warning(f"   Available repositories: {list(self._engines.keys())}")
            return {"graph_data": {"nodes": [], "edges": []}, "fallback": True, "empty": True}
        
        logger.debug(f"✓ Retrieved graph for repository: {repository_id}")
        return self._engines[repository_id]

    def export_repository_graph(self, repository_id: str) -> Dict[str, Any]:
        engine = self.get_engine(repository_id)
        
        # Fallback mode: return graph data (empty if not registered)
        if isinstance(engine, dict) and engine.get("fallback"):
            graph_data = engine.get("graph_data", {"nodes": [], "edges": []})
            is_empty = engine.get("empty", False)
            node_count = len(graph_data.get("nodes", []))
            edge_count = len(graph_data.get("edges", []))
            
            if is_empty:
                logger.error(f"❌ Exporting EMPTY graph for {repository_id} - repository not registered!")
            else:
                logger.info(f"📤 Exporting graph for {repository_id}: {node_count} nodes, {edge_count} edges")
            
            return {
                "nodes": graph_data.get("nodes", []),
                "edges": graph_data.get("edges", []),
                "node_count": node_count,
                "edge_count": edge_count,
                "validation": {"valid": not is_empty, "mode": "fallback", "empty": is_empty},
                "source": "empty-window" if not is_empty else "not_registered",
            }
        
        # Normal mode: use engine methods (type: ignore for dynamic engine)
        exported = engine.export_graph()  # type: ignore
        validation = engine.validate_graph(strict=False)  # type: ignore
        return {
            "nodes": exported["nodes"],
            "edges": exported["edges"],
            "node_count": exported["node_count"],
            "edge_count": exported["edge_count"],
            "validation": validation,
            "source": "empty-window",
        }

    def list_dependencies(self, repository_id: str) -> List[Dict[str, Any]]:
        engine = self.get_engine(repository_id)
        
        # Fallback mode: return edges from graph data (empty if not registered)
        if isinstance(engine, dict) and engine.get("fallback"):
            graph_data = engine.get("graph_data", {"nodes": [], "edges": []})
            edges = graph_data.get("edges", [])
            return [
                {
                    "source": edge["source"],
                    "target": edge["target"],
                    "relation": edge.get("relation", "depends_on"),
                    "weight": edge.get("weight", 1.0),
                }
                for edge in edges
            ]
        
        # Normal mode: use engine export (type: ignore for dynamic engine)
        exported = engine.export_graph()  # type: ignore
        return [
            {
                "source": edge["source"],
                "target": edge["target"],
                "relation": edge.get("relation", "depends_on"),
                "weight": edge.get("weight", 1.0),
            }
            for edge in exported["edges"]
        ]

    def submit_change_impact(
        self,
        repository_id: str,
        modified_file_path: str,
        change_description: str,
    ) -> str:
        engine = self.get_engine(repository_id)
        module = module_from_file_path(modified_file_path)

        # Fallback mode: return empty impacts
        if isinstance(engine, dict) and engine.get("fallback"):
            impacts: List[str] = []
            reason = f"Module '{module}' - impact analysis unavailable in fallback mode."
        else:
            # Normal mode: use engine methods (type: ignore for dynamic engine)
            if module not in engine.graph:  # type: ignore
                impacts = []
                reason = f"Module '{module}' is not in the dependency graph."
            else:
                result = engine.all_impacts(module)  # type: ignore
                impacts = result.get("all_impacts", [])
                reason = change_description or f"Transitive impact from change to {module}."

        affected = [
            {
                "module_name": name,
                "module_path": name,
                "reason": reason,
            }
            for name in impacts
        ]
        self._affected_by_repository[repository_id] = affected

        request_id = str(uuid.uuid4())
        self._impact_requests[request_id] = {
            "repository_id": repository_id,
            "modified_file_path": modified_file_path,
            "module": module,
            "change_description": change_description,
            "affected_count": len(affected),
        }
        return request_id

    def get_affected_modules(self, repository_id: str) -> List[Dict[str, str]]:
        return self._affected_by_repository.get(repository_id, [])


empty_window_engine_registry = EmptyWindowEngineRegistry()
