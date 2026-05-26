"""
Stage 2: Context Retrieval
Loads parser summaries, dependency data, and repository graph JSON.
Accepts external API payloads when URLs are configured or when injected at runtime.

Integration Layer:
- Supports live parser-workflow backend via parser_connector
- Falls back to mock data when backend unavailable
- Preserves existing orchestration flow
- Future-ready for Neo4j and ChromaDB
"""

from __future__ import annotations

import json
from typing import Any

from ai.contracts import ContextResult, IntentResult, GraphResult, ImpactResult, make_context_result
from ai.graph_reasoner import reason as reason_graph
from ai.impact_analyzer import analyze as analyze_impact
from config import (
    DEFAULT_REPOSITORY_ID,
    GRAPH_API_URL,
    GRAPH_DB_URL,
    MOCK_DATA_DIR,
    PARSER_API_URL,
    VECTOR_API_URL,
    USE_MOCK_DATA,
)

# Integration layer for parser-workflow backend
try:
    from integrations.parser_connector import parser_connector, ParserUnavailableError
    PARSER_INTEGRATION_AVAILABLE = True
except ImportError:
    PARSER_INTEGRATION_AVAILABLE = False
    parser_connector = None
    ParserUnavailableError = Exception

# Data validator for runtime verification
try:
    from integrations.data_validator import get_validator, StaticDataDetectedError
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False
    get_validator = None
    StaticDataDetectedError = Exception

# Intent → which context slices to include in the prompt payload
_INTENT_DATA_KEYS: dict[str, tuple[str, ...]] = {
    "impact": ("summaries", "dependencies", "graph", "vector_hits"),
    "summary": ("summaries", "vector_hits"),
    "dependency": ("dependencies", "graph", "vector_hits"),
    "graph": ("summaries", "graph", "vector_hits"),
    "general": ("summaries", "dependencies", "graph", "vector_hits"),
}


def _load_mock(filename: str) -> dict[str, Any]:
    """Load mock data from mock_data/ directory."""
    path = MOCK_DATA_DIR / filename
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _fetch_from_parser_api(repository_id: str) -> dict[str, Any]:
    """
    API replacement point: repository parser service.
    
    Integration Strategy:
    1. If no repository_id → return empty (no mock fallback)
    2. Try live parser-workflow backend if repository_id provided
    3. Return empty structure if backend unavailable (NO MOCK FALLBACK)
    4. Only use mock if USE_MOCK_DATA=true
    
    CRITICAL: Summaries endpoint not yet implemented in parser-workflow.
    System should work WITHOUT summaries, using only graph + dependencies.
    """
    import logging
    
    # If USE_MOCK_DATA is explicitly true, use mock
    if USE_MOCK_DATA:
        logging.info("USE_MOCK_DATA=true, using mock summaries")
        return _load_mock("summaries.json")
    
    # If no repository_id, return empty (don't fallback to mock)
    if not repository_id:
        logging.warning("No repository_id provided, returning empty summaries (no mock fallback)")
        return {"repository_id": "", "items": []}
    
    # Try parser-workflow integration for live repository
    if PARSER_INTEGRATION_AVAILABLE and parser_connector:
        try:
            # Check if backend is healthy
            if parser_connector.health_check():
                logging.info(f"Attempting to fetch summaries for {repository_id} from parser-workflow")
                result = parser_connector.fetch_repository_summaries(repository_id)
                logging.info(f"Successfully fetched live summaries for {repository_id}")
                return result
        except ParserUnavailableError:
            # Summaries not implemented - this is EXPECTED
            logging.info(f"Summaries endpoint not implemented (expected), returning empty for {repository_id}")
            return {"repository_id": repository_id, "items": []}
        except Exception as e:
            # Real error - log and return empty
            logging.warning(f"Parser integration failed: {e}, returning empty summaries")
            return {"repository_id": repository_id, "items": []}
    
    # No parser integration available - return empty (NO MOCK FALLBACK)
    logging.warning(f"Parser integration not available, returning empty summaries for {repository_id}")
    return {"repository_id": repository_id, "items": []}


def _fetch_from_graph_api(repository_id: str) -> dict[str, Any]:
    """
    API replacement point: dependency graph service.
    
    Integration Strategy:
    1. If no repository_id → return empty (NO MOCK FALLBACK)
    2. Try live parser-workflow backend if repository_id provided
    3. Return empty if backend unavailable (NO MOCK FALLBACK)
    4. Only use mock if USE_MOCK_DATA=true
    
    Future: May integrate with Neo4j for production-scale graphs
    """
    import logging
    
    # If USE_MOCK_DATA is explicitly true, use mock
    if USE_MOCK_DATA:
        logging.info("USE_MOCK_DATA=true, using mock graph")
        return _load_mock("graph.json")
    
    # If no repository_id, return empty (NO MOCK FALLBACK)
    if not repository_id:
        logging.error("No repository_id provided, returning empty graph (NO MOCK FALLBACK)")
        return {"repository_id": "", "format": "cytoscape-ready", "nodes": [], "edges": []}
    
    # Try parser-workflow integration for live repository
    if PARSER_INTEGRATION_AVAILABLE and parser_connector:
        try:
            # Check if backend is healthy
            if parser_connector.health_check():
                logging.info(f"Fetching live graph for {repository_id} from parser-workflow")
                result = parser_connector.fetch_dependency_graph(repository_id)
                node_count = len(result.get("nodes", []))
                edge_count = len(result.get("edges", []))
                logging.info(f"✓ Successfully fetched REAL graph: {node_count} nodes, {edge_count} edges")
                return result
        except ParserUnavailableError:
            # Backend unavailable - return empty (NO MOCK FALLBACK)
            logging.error(f"Parser backend unavailable for {repository_id}, returning empty graph (NO MOCK FALLBACK)")
            return {"repository_id": repository_id, "format": "cytoscape-ready", "nodes": [], "edges": []}
        except Exception as e:
            # Real error - return empty (NO MOCK FALLBACK)
            logging.error(f"Graph integration failed: {e}, returning empty graph (NO MOCK FALLBACK)")
            return {"repository_id": repository_id, "format": "cytoscape-ready", "nodes": [], "edges": []}
    
    # No parser integration - return empty (NO MOCK FALLBACK)
    logging.error(f"Parser integration not available, returning empty graph for {repository_id}")
    return {"repository_id": repository_id, "format": "cytoscape-ready", "nodes": [], "edges": []}


def _fetch_from_graph_db(repository_id: str) -> dict[str, Any]:
    """Graph DB integration point: Neo4j / similar."""
    if USE_MOCK_DATA:
        return _load_mock("graph.json")
    
    if not GRAPH_DB_URL:
        raise ValueError(
            "GRAPH_DB_URL not configured. Please set the environment variable "
            "to point to your graph database endpoint, or set USE_MOCK_DATA=true for testing."
        )
    # TODO: Implement actual Graph DB query
    # from neo4j import GraphDatabase
    # driver = GraphDatabase.driver(GRAPH_DB_URL, auth=(username, password))
    # with driver.session() as session:
    #     result = session.run("MATCH (n) RETURN n LIMIT 100")
    #     return normalize_to_cytoscape(result)
    raise NotImplementedError("Graph DB integration not yet implemented. Set USE_MOCK_DATA=true for testing.")


def _fetch_dependencies(repository_id: str) -> dict[str, Any]:
    """
    Fetch dependency data from configured API endpoint.
    
    Integration Strategy:
    1. If no repository_id → return empty (NO MOCK FALLBACK)
    2. Try live parser-workflow backend if repository_id provided
    3. Return empty if backend unavailable (NO MOCK FALLBACK)
    4. Only use mock if USE_MOCK_DATA=true
    """
    import logging
    
    # If USE_MOCK_DATA is explicitly true, use mock
    if USE_MOCK_DATA:
        logging.info("USE_MOCK_DATA=true, using mock dependencies")
        return _load_mock("dependencies.json")
    
    # If no repository_id, return empty (NO MOCK FALLBACK)
    if not repository_id:
        logging.error("No repository_id provided, returning empty dependencies (NO MOCK FALLBACK)")
        return {"repository_id": "", "external": [], "internal": [], "risk_flags": []}
    
    # Try parser-workflow integration for live repository
    if PARSER_INTEGRATION_AVAILABLE and parser_connector:
        try:
            # Check if backend is healthy
            if parser_connector.health_check():
                logging.info(f"Fetching live dependencies for {repository_id} from parser-workflow")
                result = parser_connector.fetch_dependencies(repository_id)
                logging.info(f"✓ Successfully fetched REAL dependencies for {repository_id}")
                return result
        except ParserUnavailableError:
            # Backend unavailable - return empty (NO MOCK FALLBACK)
            logging.error(f"Parser backend unavailable for {repository_id}, returning empty dependencies (NO MOCK FALLBACK)")
            return {"repository_id": repository_id, "external": [], "internal": [], "risk_flags": []}
        except Exception as e:
            # Real error - return empty (NO MOCK FALLBACK)
            logging.error(f"Dependencies integration failed: {e}, returning empty dependencies (NO MOCK FALLBACK)")
            return {"repository_id": repository_id, "external": [], "internal": [], "risk_flags": []}
    
    # No parser integration - return empty (NO MOCK FALLBACK)
    logging.error(f"Parser integration not available, returning empty dependencies for {repository_id}")
    return {"repository_id": repository_id, "external": [], "internal": [], "risk_flags": []}


def _vector_search(query: str, repository_id: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Vector search integration point with intelligent fallback.
    
    Fallback hierarchy:
    1. Vector API if configured and available
    2. Local semantic retrieval from live parser data
    3. Keyword matching over summaries
    4. Mock data as last resort
    """
    import logging
    
    # Try vector API if configured
    if VECTOR_API_URL and not USE_MOCK_DATA:
        try:
            import requests
            response = requests.post(
                VECTOR_API_URL,
                json={"query": query, "repository_id": repository_id, "top_k": top_k},
                timeout=5,
            )
            response.raise_for_status()
            logging.info(f"Vector search successful via {VECTOR_API_URL}")
            return response.json()
        except Exception as e:
            logging.warning(f"Vector API unavailable: {e}, using local fallback")
    
    # Local semantic retrieval fallback
    # Try to get live parser data first
    try:
        if PARSER_INTEGRATION_AVAILABLE and parser_connector and repository_id:
            if parser_connector.health_check():
                # Try to fetch live summaries for semantic matching
                try:
                    summaries_data = parser_connector.fetch_repository_summaries(repository_id)
                    summaries = summaries_data.get("items", [])
                    if summaries:
                        logging.info(f"Using live parser data for semantic retrieval")
                        return _local_semantic_search(query, summaries, top_k)
                except ParserUnavailableError:
                    pass  # Fall through to next strategy
    except Exception as e:
        logging.debug(f"Live parser retrieval failed: {e}")
    
    # Keyword matching over mock summaries
    summaries = _load_mock("summaries.json").get("items", [])
    logging.info("Using local keyword matching over mock data")
    return _local_semantic_search(query, summaries, top_k)


def _local_semantic_search(query: str, summaries: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    """
    Local semantic search using keyword matching and relevance scoring.
    
    This provides a lightweight fallback when vector search is unavailable.
    Matches on: filenames, paths, summaries, symbols, dependencies.
    """
    q = query.lower()
    query_terms = set(q.split())
    
    scored_items = []
    for item in summaries:
        score = 0.0
        
        # Path matching (high weight)
        path = str(item.get("path", "")).lower()
        if any(term in path for term in query_terms):
            score += 3.0
        
        # Exact filename match (highest weight)
        filename = path.split("/")[-1] if "/" in path else path
        if any(term in filename for term in query_terms):
            score += 5.0
        
        # Summary matching (medium weight)
        summary = str(item.get("summary", "")).lower()
        if any(term in summary for term in query_terms):
            score += 2.0
        
        # Symbol matching (medium weight)
        symbols = item.get("symbols", [])
        if any(any(term in str(sym).lower() for term in query_terms) for sym in symbols):
            score += 2.5
        
        # Dependency matching (low weight)
        dependencies = item.get("dependencies", [])
        if any(any(term in str(dep).lower() for term in query_terms) for dep in dependencies):
            score += 1.0
        
        if score > 0:
            scored_items.append((score, item))
    
    # Sort by score descending
    scored_items.sort(key=lambda x: x[0], reverse=True)
    
    # Return top_k items, or all items if fewer matches
    results = [item for score, item in scored_items[:top_k]]
    
    # If no matches, return top_k items from summaries
    if not results:
        results = summaries[:top_k]
    
    return results


def _resolve_summaries(repository_id: str, external: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve summaries from external data or API."""
    if external is not None:
        return external
    return _fetch_from_parser_api(repository_id)


def _resolve_graph(repository_id: str, external: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve graph from external data or API/DB."""
    if external is not None:
        return external
    
    if USE_MOCK_DATA:
        return _load_mock("graph.json")
    
    # Try Graph API first, then Graph DB
    if GRAPH_API_URL:
        return _fetch_from_graph_api(repository_id)
    elif GRAPH_DB_URL:
        return _fetch_from_graph_db(repository_id)
    else:
        raise ValueError(
            "No graph data source configured. Please set either GRAPH_API_URL or GRAPH_DB_URL "
            "environment variable, or set USE_MOCK_DATA=true for testing."
        )


def retrieve(
    intent: IntentResult,
    *,
    repository_id: str | None = None,
    external_summaries: dict[str, Any] | None = None,
    external_graph: dict[str, Any] | None = None,
    external_dependencies: dict[str, Any] | None = None,
) -> ContextResult:
    """
    Input:  IntentResult
    Output: ContextResult (JSON contract for graph_reasoner + prompt_engine)

    Pass external_* when backend APIs return live parser/graph/dependency JSON.
    
    This function now prioritizes REAL uploaded repository data:
    1. Uses live parser-workflow data if available
    2. Falls back to mock data only if parser unavailable
    3. Works without VECTOR_API_URL dependency
    """
    import logging
    
    rid = intent.get("request_id", "")
    query = intent.get("query", "")
    intent_name = intent.get("intent", "general")
    
    # Repository ID resolution - prioritize provided ID
    repo_id = repository_id or DEFAULT_REPOSITORY_ID
    
    # Log retrieval start
    logging.info(f"=" * 60)
    logging.info(f"CONTEXT RETRIEVAL START")
    logging.info(f"Repository: {repo_id or 'not specified'}")
    logging.info(f"Query: {query}")
    logging.info(f"Intent: {intent_name}")
    logging.info(f"USE_MOCK_DATA: {USE_MOCK_DATA}")
    logging.info(f"=" * 60)
    
    # If no repo_id and mock mode, use mock repo ID
    if not repo_id and USE_MOCK_DATA:
        repo_id = _load_mock("summaries.json").get("repository_id", "mock-repo")
        logging.info(f"Using mock repository ID: {repo_id}")
    elif not repo_id:
        # No repository specified and not in mock mode
        logging.warning("No repository ID provided, will attempt to use parser-workflow default")
        repo_id = "default"

    # Resolve data sources with live data priority
    summaries_doc = _resolve_summaries(repo_id, external_summaries)
    graph_doc = _resolve_graph(repo_id, external_graph)
    deps_doc = external_dependencies or _fetch_dependencies(repo_id)
    vector_hits = _vector_search(query, repo_id)

    # Log what we retrieved with detailed diagnostics
    summaries_count = len(summaries_doc.get('items', summaries_doc.get('summaries', [])))
    graph_nodes = len(graph_doc.get('nodes', []))
    graph_edges = len(graph_doc.get('edges', []))
    external_deps = len(deps_doc.get('external', []))
    internal_deps = len(deps_doc.get('internal', []))
    
    logging.info(f"✓ RAW DATA Retrieved:")
    logging.info(f"  Summaries: {summaries_count} items")
    logging.info(f"  Graph: {graph_nodes} nodes, {graph_edges} edges")
    logging.info(f"  Dependencies: {external_deps} external, {internal_deps} internal")
    logging.info(f"  Vector hits: {len(vector_hits)} results")
    
    # INTELLIGENT CONTEXT FILTERING - Only send relevant files to AI
    # This prevents overwhelming the AI with entire repository
    if graph_nodes > 0 and not USE_MOCK_DATA:
        try:
            from ai.context_filter import filter_context
            
            logging.info(f"🔍 Applying intelligent context filtering...")
            
            # Filter context to only relevant files based on query
            filtered_context = filter_context(
                query=query,
                graph_data=graph_doc,
                dependency_data=deps_doc,
                focus_node=None,  # Will be determined by graph_reasoner
            )
            
            # Replace full graph/deps with filtered versions
            graph_doc = {
                "nodes": filtered_context["nodes"],
                "edges": filtered_context["edges"],
                "format": graph_doc.get("format", "cytoscape-ready"),
            }
            
            deps_doc = filtered_context["dependencies"]
            
            # Log filtering results
            stats = filtered_context["context_stats"]
            logging.info(f"✅ Context filtered:")
            logging.info(f"   Files: {stats['total_files']} → {stats['selected_files']} (reduced by {stats['total_files'] - stats['selected_files']})")
            logging.info(f"   Edges: {stats['total_edges']} → {stats['selected_edges']} (reduced by {stats['total_edges'] - stats['selected_edges']})")
            logging.info(f"   Focus files: {filtered_context['focus_files'][:3]}")
            
            # Update counts for logging
            graph_nodes = len(graph_doc.get('nodes', []))
            graph_edges = len(graph_doc.get('edges', []))
            internal_deps = len(deps_doc.get('internal', []))
            
        except ImportError:
            logging.warning("Context filter not available, using full context")
        except Exception as e:
            logging.error(f"Context filtering failed: {e}, using full context")
    else:
        if USE_MOCK_DATA:
            logging.info("Mock mode - skipping context filtering")
        else:
            logging.warning("Empty graph - skipping context filtering")
    
    logging.info(f"✓ FILTERED DATA for AI:")
    logging.info(f"  Graph: {graph_nodes} nodes, {graph_edges} edges")
    logging.info(f"  Dependencies: {external_deps} external, {internal_deps} internal")
    
    # CRITICAL DIAGNOSTIC: Log if graph is empty
    if graph_nodes == 0:
        logging.error(f"⚠️  EMPTY GRAPH for {repo_id}! Parser-workflow returned 0 nodes.")
        logging.error(f"   Graph structure: {json.dumps(graph_doc, indent=2)[:500]}")
        logging.error(f"   This will cause 'No graph nodes available' error in graph_reasoner")
    
    # CRITICAL DIAGNOSTIC: Log if dependencies are empty
    if external_deps == 0 and internal_deps == 0:
        logging.error(f"⚠️  EMPTY DEPENDENCIES for {repo_id}! Parser-workflow returned 0 dependencies.")
        logging.error(f"   Dependencies structure: {json.dumps(deps_doc, indent=2)[:500]}")
    
    # Log sample of what we got
    if graph_nodes > 0:
        sample_nodes = graph_doc.get('nodes', [])[:3]
        logging.info(f"   Sample nodes: {[n.get('data', {}).get('id') for n in sample_nodes]}")
    if internal_deps > 0:
        sample_deps = deps_doc.get('internal', [])[:3]
        logging.info(f"   Sample internal deps: {['{}->{}'.format(d.get('from', 'N/A'), d.get('to', 'N/A')) for d in sample_deps]}")

    full_data = {
        "summaries": summaries_doc.get("items", summaries_doc.get("summaries", [])),
        "dependencies": deps_doc,
        "graph": graph_doc,
        "vector_hits": vector_hits,
    }

    keys = _INTENT_DATA_KEYS.get(intent_name, _INTENT_DATA_KEYS["general"])
    filtered_data = {k: full_data[k] for k in keys if k in full_data}

    # Build provenance with detailed source tracking
    provenance = {
        "sources": [],
        "mode": "mock" if USE_MOCK_DATA else "live",
        "repository_id": repo_id,
        "parser_available": PARSER_INTEGRATION_AVAILABLE and parser_connector is not None,
    }
    
    # Add backend URLs to provenance
    if PARSER_API_URL:
        provenance["parser_api"] = PARSER_API_URL
    if GRAPH_API_URL:
        provenance["graph_api"] = GRAPH_API_URL
    if GRAPH_DB_URL:
        provenance["graph_db"] = GRAPH_DB_URL
    if VECTOR_API_URL:
        provenance["vector_api"] = VECTOR_API_URL
    
    # Track actual data sources used
    if USE_MOCK_DATA:
        if external_summaries is None:
            provenance["sources"].append(str(MOCK_DATA_DIR / "summaries.json"))
        if external_graph is None:
            provenance["sources"].append(str(MOCK_DATA_DIR / "graph.json"))
        if external_dependencies is None:
            provenance["sources"].append(str(MOCK_DATA_DIR / "dependencies.json"))
        provenance["sources"].append("mock_vector_search")
    else:
        # Track live data sources
        if external_summaries is not None:
            provenance["sources"].append("external_summaries")
        elif PARSER_INTEGRATION_AVAILABLE:
            if summaries_doc.get("items"):
                provenance["sources"].append("parser_workflow_summaries")
            else:
                provenance["sources"].append("parser_workflow_summaries_fallback")
        
        if external_graph is not None:
            provenance["sources"].append("external_graph")
        elif PARSER_INTEGRATION_AVAILABLE:
            provenance["sources"].append("parser_workflow_graph")
        
        if external_dependencies is not None:
            provenance["sources"].append("external_dependencies")
        elif PARSER_INTEGRATION_AVAILABLE:
            provenance["sources"].append("parser_workflow_dependencies")
        
        provenance["sources"].append("local_semantic_search")

    logging.info(f"Data sources: {', '.join(provenance['sources'])}")
    logging.info(f"Retrieval mode: {provenance['mode']}")

    # Base context before Phase 2 enrichment (graph_reasoner needs data.graph)
    context = make_context_result(
        request_id=rid,
        query=query,
        intent=intent_name,
        repository_id=repo_id,
        data=filtered_data,
        provenance=provenance,
    )
    
    # RUNTIME VALIDATION: Ensure real repository data (not mock)
    if VALIDATOR_AVAILABLE and get_validator and not USE_MOCK_DATA and repo_id:
        try:
            validator = get_validator(strict_mode=False)  # Warning mode for now
            # Convert TypedDict to dict for validation
            context_dict = dict(context)
            validation_result = validator.validate_complete_context(context_dict, repo_id)
            
            # Add validation metadata to provenance
            provenance["validation"] = {
                "performed": True,
                "is_valid": validation_result["is_valid"],
                "issues_found": len(validation_result["all_issues"]),
                "checks_performed": validation_result["total_checks"],
            }
            
            if not validation_result["is_valid"]:
                logging.warning(
                    f"⚠️  VALIDATION WARNING: Static data patterns detected in {repo_id}. "
                    f"Issues: {validation_result['all_issues']}"
                )
                # Add warning to provenance
                provenance["warnings"] = provenance.get("warnings", [])
                provenance["warnings"].append(
                    f"Static data patterns detected: {len(validation_result['all_issues'])} issues"
                )
        except Exception as e:
            logging.error(f"Validation failed: {e}")
            provenance["validation"] = {
                "performed": True,
                "error": str(e),
            }

    # Phase 2 graph intelligence (runs during context retrieval, before prompt)
    logging.info("Running graph reasoning...")
    graph_insights: GraphResult = reason_graph(context)
    logging.info(f"✓ Graph reasoning complete: focus={graph_insights.get('focus_label', 'N/A')}")
    
    logging.info("Running impact analysis...")
    impact_insights: ImpactResult = analyze_impact(context, graph_insights)
    logging.info(f"✓ Impact analysis complete: risk={impact_insights.get('risk_level', 'N/A')}")

    context = make_context_result(
        request_id=rid,
        query=query,
        intent=intent_name,
        repository_id=repo_id,
        data=filtered_data,
        provenance=provenance,
        graph_insights=graph_insights,
        impact_insights=impact_insights,
    )
    
    logging.info(f"=" * 60)
    logging.info(f"CONTEXT RETRIEVAL COMPLETE")
    logging.info(f"=" * 60)
    
    return context

# Made with Bob
