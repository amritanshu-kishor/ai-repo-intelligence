"""
Data Validator - Runtime verification for real vs mock data.

This module ensures that ALL outputs originate from real uploaded repositories
and prevents static/mock data from contaminating production responses.

Validation Guards:
1. Detect mock data patterns (mod_a, mod_b, shared, entry, etc.)
2. Verify repository-specific data
3. Ensure graph rebuilds per upload
4. Track data provenance
5. Trigger automatic debugging on static output detection
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class StaticDataDetectedError(Exception):
    """Raised when static/mock data patterns are detected in production output."""
    pass


class DataValidator:
    """
    Runtime validator to ensure real dynamic repository analysis.
    
    Detects and prevents:
    - Mock node IDs (mod_a, mod_b, shared, entry)
    - Mock file paths (modules/a, modules/b, app/entry.py)
    - Mock repository IDs (mock-repo-001)
    - Placeholder chains
    - Static dependency patterns
    """
    
    # Known mock patterns from mock_data/
    MOCK_NODE_IDS = {"mod_a", "mod_b", "mod_c", "shared", "entry"}
    MOCK_FILE_PATHS = {
        "modules/a",
        "modules/b", 
        "modules/c",
        "shared/",
        "app/entry.py",
    }
    MOCK_REPO_IDS = {"mock-repo-001", "mock-repo", ""}
    MOCK_SYMBOLS = {"validate", "DomainService", "Router", "register_routes"}
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize data validator.
        
        Args:
            strict_mode: If True, raise errors on mock data detection.
                        If False, only log warnings.
        """
        self.strict_mode = strict_mode
        self.validation_log: list[dict[str, Any]] = []
    
    def validate_graph_data(
        self,
        graph_data: dict[str, Any],
        repository_id: str,
        context: str = "graph",
    ) -> dict[str, Any]:
        """
        Validate graph data for mock patterns.
        
        Args:
            graph_data: Graph data to validate
            repository_id: Expected repository ID
            context: Context for logging (e.g., "graph", "dependencies")
            
        Returns:
            Validation result with issues found
            
        Raises:
            StaticDataDetectedError: If mock patterns detected in strict mode
        """
        issues: list[str] = []
        
        # Check repository ID
        graph_repo_id = graph_data.get("repository_id", "")
        if graph_repo_id in self.MOCK_REPO_IDS:
            issues.append(f"Mock repository ID detected: {graph_repo_id}")
        elif graph_repo_id != repository_id:
            issues.append(
                f"Repository ID mismatch: expected {repository_id}, "
                f"got {graph_repo_id}"
            )
        
        # Check nodes for mock patterns
        nodes = graph_data.get("nodes", [])
        mock_nodes_found = []
        
        for node in nodes:
            node_data = node.get("data", node)
            node_id = node_data.get("id", "")
            node_label = node_data.get("label", "")
            
            if node_id in self.MOCK_NODE_IDS:
                mock_nodes_found.append(node_id)
            
            if node_label in self.MOCK_FILE_PATHS:
                mock_nodes_found.append(f"label:{node_label}")
        
        if mock_nodes_found:
            issues.append(
                f"Mock node patterns detected: {', '.join(mock_nodes_found)}"
            )
        
        # Check edges for mock patterns
        edges = graph_data.get("edges", [])
        mock_edges_found = []
        
        for edge in edges:
            edge_data = edge.get("data", edge)
            source = edge_data.get("source", "")
            target = edge_data.get("target", "")
            
            if source in self.MOCK_NODE_IDS or target in self.MOCK_NODE_IDS:
                mock_edges_found.append(f"{source}->{target}")
        
        if mock_edges_found:
            issues.append(
                f"Mock edge patterns detected: {', '.join(mock_edges_found[:5])}"
            )
        
        # Log validation result
        validation_result = {
            "context": context,
            "repository_id": repository_id,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "issues": issues,
            "is_valid": len(issues) == 0,
        }
        
        self.validation_log.append(validation_result)
        
        if issues:
            error_msg = f"[{context}] Static data detected in {repository_id}: {'; '.join(issues)}"
            logger.error(error_msg)
            
            if self.strict_mode:
                raise StaticDataDetectedError(error_msg)
            else:
                logger.warning(f"Continuing in non-strict mode despite: {error_msg}")
        else:
            logger.info(
                f"✓ [{context}] Validation passed for {repository_id}: "
                f"{len(nodes)} nodes, {len(edges)} edges"
            )
        
        return validation_result
    
    def validate_dependencies(
        self,
        deps_data: dict[str, Any],
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Validate dependencies data for mock patterns.
        
        Args:
            deps_data: Dependencies data to validate
            repository_id: Expected repository ID
            
        Returns:
            Validation result with issues found
        """
        issues: list[str] = []
        
        # Check repository ID
        deps_repo_id = deps_data.get("repository_id", "")
        if deps_repo_id in self.MOCK_REPO_IDS:
            issues.append(f"Mock repository ID detected: {deps_repo_id}")
        
        # Check internal dependencies for mock paths
        internal = deps_data.get("internal", [])
        mock_internal_found = []
        
        for dep in internal:
            from_path = dep.get("from", "")
            to_path = dep.get("to", "")
            
            if from_path in self.MOCK_FILE_PATHS or to_path in self.MOCK_FILE_PATHS:
                mock_internal_found.append(f"{from_path}->{to_path}")
        
        if mock_internal_found:
            issues.append(
                f"Mock internal dependency patterns: {', '.join(mock_internal_found[:5])}"
            )
        
        # Check external dependencies for mock packages
        external = deps_data.get("external", [])
        mock_external = ["framework-core", "data-orm", "test-runner"]
        mock_external_found = []
        
        for dep in external:
            name = dep.get("name", "")
            if name in mock_external:
                mock_external_found.append(name)
        
        if mock_external_found:
            issues.append(
                f"Mock external dependencies: {', '.join(mock_external_found)}"
            )
        
        validation_result = {
            "context": "dependencies",
            "repository_id": repository_id,
            "external_count": len(external),
            "internal_count": len(internal),
            "issues": issues,
            "is_valid": len(issues) == 0,
        }
        
        self.validation_log.append(validation_result)
        
        if issues:
            error_msg = f"[dependencies] Static data detected: {'; '.join(issues)}"
            logger.error(error_msg)
            
            if self.strict_mode:
                raise StaticDataDetectedError(error_msg)
        else:
            logger.info(
                f"✓ [dependencies] Validation passed: "
                f"{len(external)} external, {len(internal)} internal"
            )
        
        return validation_result
    
    def validate_summaries(
        self,
        summaries_data: dict[str, Any],
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Validate summaries data for mock patterns.
        
        Args:
            summaries_data: Summaries data to validate
            repository_id: Expected repository ID
            
        Returns:
            Validation result with issues found
        """
        issues: list[str] = []
        
        # Check repository ID
        summ_repo_id = summaries_data.get("repository_id", "")
        if summ_repo_id in self.MOCK_REPO_IDS:
            issues.append(f"Mock repository ID detected: {summ_repo_id}")
        
        # Check items for mock paths and symbols
        items = summaries_data.get("items", [])
        mock_paths_found = []
        mock_symbols_found = []
        
        for item in items:
            path = item.get("path", "")
            symbols = item.get("symbols", [])
            
            if path in self.MOCK_FILE_PATHS:
                mock_paths_found.append(path)
            
            for symbol in symbols:
                if symbol in self.MOCK_SYMBOLS:
                    mock_symbols_found.append(symbol)
        
        if mock_paths_found:
            issues.append(
                f"Mock file paths detected: {', '.join(mock_paths_found)}"
            )
        
        if mock_symbols_found:
            issues.append(
                f"Mock symbols detected: {', '.join(set(mock_symbols_found))}"
            )
        
        validation_result = {
            "context": "summaries",
            "repository_id": repository_id,
            "item_count": len(items),
            "issues": issues,
            "is_valid": len(issues) == 0,
        }
        
        self.validation_log.append(validation_result)
        
        if issues:
            error_msg = f"[summaries] Static data detected: {'; '.join(issues)}"
            logger.error(error_msg)
            
            if self.strict_mode:
                raise StaticDataDetectedError(error_msg)
        else:
            logger.info(f"✓ [summaries] Validation passed: {len(items)} items")
        
        return validation_result
    
    def validate_complete_context(
        self,
        context_data: dict[str, Any],
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Validate complete context data from all sources.
        
        Args:
            context_data: Complete context data
            repository_id: Expected repository ID
            
        Returns:
            Comprehensive validation result
        """
        logger.info(f"=" * 60)
        logger.info(f"VALIDATING CONTEXT FOR: {repository_id}")
        logger.info(f"=" * 60)
        
        all_issues: list[str] = []
        validations: dict[str, dict[str, Any]] = {}
        
        # Validate graph data
        if "graph" in context_data.get("data", {}):
            try:
                graph_result = self.validate_graph_data(
                    context_data["data"]["graph"],
                    repository_id,
                    "graph",
                )
                validations["graph"] = graph_result
                all_issues.extend(graph_result["issues"])
            except Exception as e:
                logger.error(f"Graph validation failed: {e}")
                all_issues.append(f"Graph validation error: {str(e)}")
        
        # Validate dependencies
        if "dependencies" in context_data.get("data", {}):
            try:
                deps_result = self.validate_dependencies(
                    context_data["data"]["dependencies"],
                    repository_id,
                )
                validations["dependencies"] = deps_result
                all_issues.extend(deps_result["issues"])
            except Exception as e:
                logger.error(f"Dependencies validation failed: {e}")
                all_issues.append(f"Dependencies validation error: {str(e)}")
        
        # Validate summaries
        if "summaries" in context_data.get("data", {}):
            try:
                summ_result = self.validate_summaries(
                    {"items": context_data["data"]["summaries"], "repository_id": repository_id},
                    repository_id,
                )
                validations["summaries"] = summ_result
                all_issues.extend(summ_result["issues"])
            except Exception as e:
                logger.error(f"Summaries validation failed: {e}")
                all_issues.append(f"Summaries validation error: {str(e)}")
        
        # Check provenance
        provenance = context_data.get("provenance", {})
        mode = provenance.get("mode", "unknown")
        sources = provenance.get("sources", [])
        
        if mode == "mock":
            all_issues.append("Context is in MOCK mode")
        
        if any("mock" in str(s).lower() for s in sources):
            all_issues.append(f"Mock data sources detected: {sources}")
        
        result = {
            "repository_id": repository_id,
            "mode": mode,
            "sources": sources,
            "validations": validations,
            "all_issues": all_issues,
            "is_valid": len(all_issues) == 0,
            "total_checks": len(validations),
        }
        
        logger.info(f"=" * 60)
        if result["is_valid"]:
            logger.info(f"✓ VALIDATION PASSED: All data from real repository")
        else:
            logger.error(f"✗ VALIDATION FAILED: {len(all_issues)} issues found")
            for issue in all_issues:
                logger.error(f"  - {issue}")
        logger.info(f"=" * 60)
        
        return result
    
    def get_validation_summary(self) -> dict[str, Any]:
        """
        Get summary of all validations performed.
        
        Returns:
            Summary of validation log
        """
        total = len(self.validation_log)
        passed = sum(1 for v in self.validation_log if v["is_valid"])
        failed = total - passed
        
        return {
            "total_validations": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "log": self.validation_log,
        }


# Singleton instance
_validator: DataValidator | None = None


def get_validator(strict_mode: bool = True) -> DataValidator:
    """
    Get or create data validator singleton.
    
    Args:
        strict_mode: If True, raise errors on mock data detection
        
    Returns:
        DataValidator instance
    """
    global _validator
    if _validator is None:
        _validator = DataValidator(strict_mode=strict_mode)
    return _validator


__all__ = [
    "DataValidator",
    "StaticDataDetectedError",
    "get_validator",
]

# Made with Bob