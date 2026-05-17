"""
Repository Session Manager - Ensures proper isolation between uploaded repositories.

This module manages repository sessions to guarantee that:
1. Each uploaded ZIP creates a NEW repository session
2. Previous graph/context data is invalidated
3. No data leakage between repositories
4. Session metadata is tracked
5. Automatic cleanup of old sessions
"""

from __future__ import annotations

import datetime
import logging
from typing import Any
from pathlib import Path

logger = logging.getLogger(__name__)


class RepositorySession:
    """
    Represents a single repository upload session.
    
    Each session tracks:
    - Repository ID and upload timestamp
    - File count and processing status
    - Graph/dependency/summary availability
    - Data source provenance
    - Validation results
    """
    
    def __init__(
        self,
        repository_id: str,
        upload_path: Path | str,
        file_count: int = 0,
    ):
        """
        Initialize repository session.
        
        Args:
            repository_id: Unique identifier for this repository
            upload_path: Path where repository was extracted
            file_count: Number of source files found
        """
        self.repository_id = repository_id
        self.upload_path = Path(upload_path)
        self.file_count = file_count
        self.upload_timestamp = datetime.datetime.utcnow()
        self.last_query_timestamp: datetime.datetime | None = None
        
        # Processing status
        self.parser_indexed = False
        self.parser_ready = False
        self.graph_available = False
        self.dependencies_available = False
        self.summaries_available = False
        
        # Data metrics
        self.graph_node_count = 0
        self.graph_edge_count = 0
        self.external_dep_count = 0
        self.internal_dep_count = 0
        
        # Validation tracking
        self.validation_performed = False
        self.validation_passed = False
        self.validation_issues: list[str] = []
        
        # Query history
        self.query_count = 0
        self.queries: list[dict[str, Any]] = []
        
        logger.info(
            f"Created new repository session: {repository_id} "
            f"({file_count} files)"
        )
    
    def update_parser_status(
        self,
        indexed: bool,
        ready: bool,
        graph_available: bool = False,
        dependencies_available: bool = False,
    ) -> None:
        """Update parser-workflow processing status."""
        self.parser_indexed = indexed
        self.parser_ready = ready
        self.graph_available = graph_available
        self.dependencies_available = dependencies_available
        
        logger.info(
            f"Parser status updated for {self.repository_id}: "
            f"indexed={indexed}, ready={ready}, "
            f"graph={graph_available}, deps={dependencies_available}"
        )
    
    def update_graph_metrics(self, node_count: int, edge_count: int) -> None:
        """Update graph metrics from parser-workflow."""
        self.graph_node_count = node_count
        self.graph_edge_count = edge_count
        self.graph_available = node_count > 0
        
        logger.info(
            f"Graph metrics updated for {self.repository_id}: "
            f"{node_count} nodes, {edge_count} edges"
        )
    
    def update_dependency_metrics(
        self,
        external_count: int,
        internal_count: int,
    ) -> None:
        """Update dependency metrics from parser-workflow."""
        self.external_dep_count = external_count
        self.internal_dep_count = internal_count
        self.dependencies_available = (external_count + internal_count) > 0
        
        logger.info(
            f"Dependency metrics updated for {self.repository_id}: "
            f"{external_count} external, {internal_count} internal"
        )
    
    def record_validation(
        self,
        passed: bool,
        issues: list[str] | None = None,
    ) -> None:
        """Record validation results."""
        self.validation_performed = True
        self.validation_passed = passed
        self.validation_issues = issues or []
        
        if passed:
            logger.info(f"✓ Validation passed for {self.repository_id}")
        else:
            logger.warning(
                f"✗ Validation failed for {self.repository_id}: "
                f"{len(self.validation_issues)} issues"
            )
    
    def record_query(self, query: str, intent: str, result: dict[str, Any]) -> None:
        """Record a query against this repository."""
        self.query_count += 1
        self.last_query_timestamp = datetime.datetime.utcnow()
        
        self.queries.append({
            "timestamp": self.last_query_timestamp.isoformat(),
            "query": query,
            "intent": intent,
            "data_source": result.get("data_source", "unknown"),
            "validation_passed": result.get("validation_passed", False),
        })
        
        # Keep only last 50 queries
        if len(self.queries) > 50:
            self.queries = self.queries[-50:]
    
    def is_ready(self) -> bool:
        """Check if repository is ready for queries."""
        return (
            self.parser_ready and
            self.graph_available and
            self.dependencies_available
        )
    
    def get_status(self) -> dict[str, Any]:
        """Get complete session status."""
        return {
            "repository_id": self.repository_id,
            "upload_timestamp": self.upload_timestamp.isoformat(),
            "last_query_timestamp": (
                self.last_query_timestamp.isoformat()
                if self.last_query_timestamp
                else None
            ),
            "file_count": self.file_count,
            "processing": {
                "parser_indexed": self.parser_indexed,
                "parser_ready": self.parser_ready,
                "graph_available": self.graph_available,
                "dependencies_available": self.dependencies_available,
                "summaries_available": self.summaries_available,
                "is_ready": self.is_ready(),
            },
            "metrics": {
                "graph_nodes": self.graph_node_count,
                "graph_edges": self.graph_edge_count,
                "external_dependencies": self.external_dep_count,
                "internal_dependencies": self.internal_dep_count,
            },
            "validation": {
                "performed": self.validation_performed,
                "passed": self.validation_passed,
                "issues_count": len(self.validation_issues),
                "issues": self.validation_issues[:5],  # First 5 issues
            },
            "usage": {
                "query_count": self.query_count,
                "recent_queries": self.queries[-5:],  # Last 5 queries
            },
        }


class RepositorySessionManager:
    """
    Manages multiple repository sessions with automatic cleanup.
    
    Ensures:
    - Each upload creates a new session
    - Old sessions are invalidated
    - No data leakage between repositories
    - Session history is maintained
    """
    
    def __init__(self, max_sessions: int = 10):
        """
        Initialize session manager.
        
        Args:
            max_sessions: Maximum number of sessions to keep in memory
        """
        self.max_sessions = max_sessions
        self.sessions: dict[str, RepositorySession] = {}
        self.active_repository_id: str | None = None
        
        logger.info(f"Repository session manager initialized (max: {max_sessions})")
    
    def create_session(
        self,
        repository_id: str,
        upload_path: Path | str,
        file_count: int = 0,
    ) -> RepositorySession:
        """
        Create a new repository session.
        
        This INVALIDATES any previous session for the same repository_id.
        
        Args:
            repository_id: Unique identifier for repository
            upload_path: Path where repository was extracted
            file_count: Number of source files
            
        Returns:
            New RepositorySession instance
        """
        # Invalidate previous session if exists
        if repository_id in self.sessions:
            logger.warning(
                f"Invalidating previous session for {repository_id} "
                f"(uploaded {self.sessions[repository_id].upload_timestamp})"
            )
            del self.sessions[repository_id]
        
        # Create new session
        session = RepositorySession(repository_id, upload_path, file_count)
        self.sessions[repository_id] = session
        self.active_repository_id = repository_id
        
        # Cleanup old sessions if needed
        if len(self.sessions) > self.max_sessions:
            self._cleanup_old_sessions()
        
        logger.info(
            f"✓ New session created: {repository_id} "
            f"(total sessions: {len(self.sessions)})"
        )
        
        return session
    
    def get_session(self, repository_id: str) -> RepositorySession | None:
        """Get existing session by repository ID."""
        return self.sessions.get(repository_id)
    
    def get_active_session(self) -> RepositorySession | None:
        """Get currently active session."""
        if self.active_repository_id:
            return self.sessions.get(self.active_repository_id)
        return None
    
    def set_active_repository(self, repository_id: str) -> bool:
        """
        Set active repository for queries.
        
        Args:
            repository_id: Repository to make active
            
        Returns:
            True if repository exists and was set active
        """
        if repository_id in self.sessions:
            self.active_repository_id = repository_id
            logger.info(f"Active repository set to: {repository_id}")
            return True
        
        logger.warning(f"Cannot set active repository: {repository_id} not found")
        return False
    
    def _cleanup_old_sessions(self) -> None:
        """Remove oldest sessions to stay within max_sessions limit."""
        if len(self.sessions) <= self.max_sessions:
            return
        
        # Sort by upload timestamp
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1].upload_timestamp,
        )
        
        # Remove oldest sessions
        to_remove = len(self.sessions) - self.max_sessions
        for repo_id, session in sorted_sessions[:to_remove]:
            logger.info(
                f"Removing old session: {repo_id} "
                f"(uploaded {session.upload_timestamp})"
            )
            del self.sessions[repo_id]
    
    def get_all_sessions(self) -> dict[str, dict[str, Any]]:
        """Get status of all sessions."""
        return {
            repo_id: session.get_status()
            for repo_id, session in self.sessions.items()
        }
    
    def get_summary(self) -> dict[str, Any]:
        """Get manager summary."""
        return {
            "total_sessions": len(self.sessions),
            "active_repository": self.active_repository_id,
            "max_sessions": self.max_sessions,
            "sessions": list(self.sessions.keys()),
        }


# Singleton instance
_session_manager: RepositorySessionManager | None = None


def get_session_manager() -> RepositorySessionManager:
    """
    Get or create repository session manager singleton.
    
    Returns:
        RepositorySessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = RepositorySessionManager()
    return _session_manager


__all__ = [
    "RepositorySession",
    "RepositorySessionManager",
    "get_session_manager",
]

# Made with Bob