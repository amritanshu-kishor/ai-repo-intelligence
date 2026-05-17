"""
FIXED VERSION - Stage 2: Context Retrieval with Live Data Support

This file contains the fixed versions of the fetch functions that properly
use live data from parser-workflow when available.

To apply: Copy the functions below into context_builder.py, replacing the
existing versions of _fetch_from_parser_api, _fetch_from_graph_api, and _fetch_dependencies.
"""

import logging

logger = logging.getLogger(__name__)


def _fetch_from_parser_api_FIXED(repository_id: str) -> dict[str, Any]:
    """
    API replacement point: repository parser service.
    
    Integration Strategy:
    1. If no repository_id → use mock data
    2. Try live parser-workflow backend if repository_id provided
    3. Fall back to mock data if backend unavailable
    4. Preserve existing behavior when USE_MOCK_DATA=true
    """
    # If no repository_id, use mock data
    if not repository_id:
        logger.info("No repository_id provided, using mock summaries")
        return _load_mock("summaries.json")
    
    # If USE_MOCK_DATA is explicitly true, use mock
    if USE_MOCK_DATA:
        logger.info("USE_MOCK_DATA=true, using mock summaries")
        return _load_mock("summaries.json")
    
    # Try parser-workflow integration for live repository
    if PARSER_INTEGRATION_AVAILABLE and parser_connector:
        try:
            # Check if backend is healthy
            if parser_connector.health_check():
                logger.info(f"Attempting to fetch summaries for {repository_id} from parser-workflow")
                result = parser_connector.fetch_repository_summaries(repository_id)
                logger.info(f"Successfully fetched live summaries for {repository_id}")
                return result
        except ParserUnavailableError:
            # Backend unavailable, fall through to mock
            logger.warning("Parser backend unavailable, falling back to mock summaries")
        except Exception as e:
            # Log but don't fail - fall through to mock
            logger.warning(f"Parser integration failed: {e}, falling back to mock summaries")
    
    # Fallback to mock data (summaries endpoint not yet implemented)
    logger.info(f"Parser summaries not available for {repository_id}, using mock data")
    return _load_mock("summaries.json")


def _fetch_from_graph_api_FIXED(repository_id: str) -> dict[str, Any]:
    """
    API replacement point: dependency graph service.
    
    Integration Strategy:
    1. If no repository_id → use mock data
    2. Try live parser-workflow backend if repository_id provided
    3. Fall back to mock data if backend unavailable
    4. Preserve existing behavior when USE_MOCK_DATA=true
    
    Future: May integrate with Neo4j for production-scale graphs
    """
    # If no repository_id, use mock data
    if not repository_id:
        logger.info("No repository_id provided, using mock graph")
        return _load_mock("graph.json")
    
    # If USE_MOCK_DATA is explicitly true, use mock
    if USE_MOCK_DATA:
        logger.info("USE_MOCK_DATA=true, using mock graph")
        return _load_mock("graph.json")
    
    # Try parser-workflow integration for live repository
    if PARSER_INTEGRATION_AVAILABLE and parser_connector:
        try:
            # Check if backend is healthy
            if parser_connector.health_check():
                logger.info(f"Fetching live graph for {repository_id} from parser-workflow")
                result = parser_connector.fetch_dependency_graph(repository_id)
                node_count = len(result.get("nodes", []))
                edge_count = len(result.get("edges", []))
                logger.info(f"Successfully fetched live graph: {node_count} nodes, {edge_count} edges")
                return result
        except ParserUnavailableError:
            # Backend unavailable, fall through to mock
            logger.warning("Parser backend unavailable, falling back to mock graph")
        except Exception as e:
            # Log but don't fail - fall through to mock
            logger.warning(f"Graph integration failed: {e}, falling back to mock graph")
    
    # Fallback to mock data
    logger.info(f"Live graph not available for {repository_id}, using mock data")
    return _load_mock("graph.json")


def _fetch_dependencies_FIXED(repository_id: str) -> dict[str, Any]:
    """
    Fetch dependency data from configured API endpoint.
    
    Integration Strategy:
    1. If no repository_id → use mock data
    2. Try live parser-workflow backend if repository_id provided
    3. Fall back to mock data if backend unavailable
    4. Preserve existing behavior when USE_MOCK_DATA=true
    """
    # If no repository_id, use mock data
    if not repository_id:
        logger.info("No repository_id provided, using mock dependencies")
        return _load_mock("dependencies.json")
    
    # If USE_MOCK_DATA is explicitly true, use mock
    if USE_MOCK_DATA:
        logger.info("USE_MOCK_DATA=true, using mock dependencies")
        return _load_mock("dependencies.json")
    
    # Try parser-workflow integration for live repository
    if PARSER_INTEGRATION_AVAILABLE and parser_connector:
        try:
            # Check if backend is healthy
            if parser_connector.health_check():
                logger.info(f"Fetching live dependencies for {repository_id} from parser-workflow")
                result = parser_connector.fetch_dependencies(repository_id)
                logger.info(f"Successfully fetched live dependencies for {repository_id}")
                return result
        except ParserUnavailableError:
            # Backend unavailable, fall through to mock
            logger.warning("Parser backend unavailable, falling back to mock dependencies")
        except Exception as e:
            # Log but don't fail - fall through to mock
            logger.warning(f"Dependencies integration failed: {e}, falling back to mock dependencies")
    
    # Fallback to mock data
    logger.info(f"Live dependencies not available for {repository_id}, using mock data")
    return _load_mock("dependencies.json")


# INSTRUCTIONS TO APPLY:
# 1. Open repo-ai/ai/context_builder.py
# 2. Find the function _fetch_from_parser_api (around line 56)
# 3. Replace it with _fetch_from_parser_api_FIXED above (remove _FIXED suffix)
# 4. Find the function _fetch_from_graph_api (around line 97)
# 5. Replace it with _fetch_from_graph_api_FIXED above (remove _FIXED suffix)
# 6. Find the function _fetch_dependencies (around line 157)
# 7. Replace it with _fetch_dependencies_FIXED above (remove _FIXED suffix)
# 8. Save the file

# Made with Bob
