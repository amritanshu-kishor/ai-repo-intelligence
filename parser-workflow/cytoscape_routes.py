"""
Cytoscape Graph Routes
Handles graph visualization, streaming, analytics, and comparison endpoints
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
import asyncio
import json

from networkx_service import networkx_service
from analytics_service import analytics_service
from logger import get_logger

logger = get_logger()

router = APIRouter(tags=["cytoscape"])


@router.get("/api/v1/graph/cytoscape/{repository_id}")
async def get_cytoscape_graph(repository_id: str) -> Dict[str, Any]:
    """
    Get repository graph in Cytoscape.js format
    
    Returns graph with nodes and edges formatted for Cytoscape visualization
    """
    try:
        G = networkx_service.get_graph(repository_id)
        
        if not G:
            raise HTTPException(
                status_code=404,
                detail=f"Graph not found for repository: {repository_id}"
            )
        
        # Convert to Cytoscape format
        cytoscape_data = networkx_service.to_cytoscape_format(G)
        
        # Extract nodes and edges from elements array for repo-ai compatibility
        elements = cytoscape_data.get("elements", [])
        nodes = [elem for elem in elements if "source" not in elem.get("data", {})]
        edges = [elem for elem in elements if "source" in elem.get("data", {})]
        
        # Calculate metrics
        metrics = networkx_service.calculate_metrics(G)
        
        # Get node statistics
        node_stats = networkx_service.get_node_statistics(G)
        
        logger.info(f"📤 Returning graph for {repository_id}: {len(nodes)} nodes, {len(edges)} edges")
        
        # Debug logging for edge verification
        if edges:
            logger.info(f"   🔍 Sample edges being returned: {edges[:3]}")
        else:
            logger.warning(f"   ⚠️  NO EDGES being returned! NetworkX graph has {G.number_of_edges()} edges")
            logger.warning(f"   🔍 Elements array has {len(elements)} items")
            logger.warning(f"   🔍 Checking elements structure...")
            for i, elem in enumerate(elements[:5]):
                has_source = "source" in elem.get("data", {})
                logger.warning(f"      Element {i}: has_source={has_source}, data keys={list(elem.get('data', {}).keys())}")
        
        return {
            "repository_id": repository_id,
            "graph": {
                "elements": elements,  # Original Cytoscape format
                "nodes": nodes,        # Separated for repo-ai
                "edges": edges         # Separated for repo-ai
            },
            "metrics": metrics,
            "node_statistics": node_stats,
            "layout_options": ["cose", "breadthfirst", "concentric", "circle", "grid"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Cytoscape graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/graph/create/{repository_id}")
async def create_graph(
    repository_id: str,
    dependencies: List[Dict[str, Any]],
    parsed_files: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a new NetworkX graph from parsed repository data
    
    Args:
        repository_id: Unique repository identifier
        dependencies: List of dependency edges
        parsed_files: List of parsed file metadata
    """
    try:
        # Create graph
        G = networkx_service.create_graph_from_dependencies(
            repository_id,
            dependencies,
            parsed_files
        )
        
        # Convert to Cytoscape format
        cytoscape_data = networkx_service.to_cytoscape_format(G)
        
        # Calculate metrics
        metrics = networkx_service.calculate_metrics(G)
        
        return {
            "repository_id": repository_id,
            "status": "created",
            "graph": cytoscape_data,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error creating graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/api/v1/stream/graph/{repository_id}")
async def stream_graph(websocket: WebSocket, repository_id: str):
    """
    WebSocket endpoint for real-time graph streaming
    
    Streams nodes and edges gradually for animated visualization
    """
    await websocket.accept()
    
    try:
        G = networkx_service.get_graph(repository_id)
        
        if not G:
            await websocket.send_json({
                "type": "error",
                "message": f"Graph not found for repository: {repository_id}"
            })
            await websocket.close()
            return
        
        # Send initial status
        await websocket.send_json({
            "type": "start",
            "data": {
                "repository_id": repository_id,
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges()
            }
        })
        
        # Generate and stream events
        events = await networkx_service.generate_streaming_events(G, delay=0.05)
        
        for event in events:
            await websocket.send_json(event)
        
        logger.info(f"Completed streaming graph for {repository_id}")
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {repository_id}")
    except Exception as e:
        logger.error(f"Error streaming graph: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.get("/api/v1/analytics/{repository_id}")
async def get_analytics(repository_id: str) -> Dict[str, Any]:
    """
    Get comprehensive analytics for a repository
    
    Returns all chart data for Chart.js visualization
    """
    try:
        # Check cache first
        cached = analytics_service.get_cached_analytics(repository_id)
        if cached:
            return cached
        
        # Get graph
        G = networkx_service.get_graph(repository_id)
        
        if not G:
            raise HTTPException(
                status_code=404,
                detail=f"Graph not found for repository: {repository_id}"
            )
        
        # Get parsed files data (mock for now - should come from parser service)
        parsed_files = []
        for node, attrs in G.nodes(data=True):
            if attrs.get("node_type") == "file":
                parsed_files.append({
                    "file": node,
                    "language": attrs.get("language", "unknown"),
                    "imports": [],
                    "functions": [],
                    "classes": [],
                    "loc": attrs.get("loc", 0)
                })
        
        # Generate analytics
        analytics = analytics_service.generate_all_analytics(G, parsed_files, repository_id)
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/comparison/{repo_id_1}/{repo_id_2}")
async def compare_repositories(repo_id_1: str, repo_id_2: str) -> Dict[str, Any]:
    """
    Compare two repository graphs
    
    Returns comparison metrics and differences
    """
    try:
        comparison = networkx_service.compare_graphs(repo_id_1, repo_id_2)
        
        if "error" in comparison:
            raise HTTPException(status_code=404, detail=comparison["error"])
        
        # Get both graphs in Cytoscape format
        G1 = networkx_service.get_graph(repo_id_1)
        G2 = networkx_service.get_graph(repo_id_2)
        
        comparison["graph_1"] = networkx_service.to_cytoscape_format(G1) if G1 else None
        comparison["graph_2"] = networkx_service.to_cytoscape_format(G2) if G2 else None
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/graph/{repository_id}/metrics")
async def get_graph_metrics(repository_id: str) -> Dict[str, Any]:
    """Get detailed graph metrics and statistics"""
    try:
        G = networkx_service.get_graph(repository_id)
        
        if not G:
            raise HTTPException(
                status_code=404,
                detail=f"Graph not found for repository: {repository_id}"
            )
        
        metrics = networkx_service.calculate_metrics(G)
        node_stats = networkx_service.get_node_statistics(G)
        
        return {
            "repository_id": repository_id,
            "metrics": metrics,
            "node_statistics": node_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/graph/{repository_id}/cycles")
async def get_circular_dependencies(repository_id: str) -> Dict[str, Any]:
    """Find circular dependencies in the graph"""
    try:
        G = networkx_service.get_graph(repository_id)
        
        if not G:
            raise HTTPException(
                status_code=404,
                detail=f"Graph not found for repository: {repository_id}"
            )
        
        cycles = networkx_service.find_circular_dependencies(G)
        
        return {
            "repository_id": repository_id,
            "cycle_count": len(cycles),
            "cycles": cycles[:10],  # Return first 10 cycles
            "has_cycles": len(cycles) > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding cycles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/graph/{repository_id}/tree/{node_id}")
async def get_dependency_tree(
    repository_id: str,
    node_id: str,
    max_depth: int = 3
) -> Dict[str, Any]:
    """Get dependency tree starting from a specific node"""
    try:
        G = networkx_service.get_graph(repository_id)
        
        if not G:
            raise HTTPException(
                status_code=404,
                detail=f"Graph not found for repository: {repository_id}"
            )
        
        tree = networkx_service.get_dependency_tree(G, node_id, max_depth)
        
        if not tree:
            raise HTTPException(
                status_code=404,
                detail=f"Node not found: {node_id}"
            )
        
        return {
            "repository_id": repository_id,
            "root_node": node_id,
            "max_depth": max_depth,
            "tree": tree
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dependency tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/embeddings/similarity/{repository_id}")
async def get_embedding_similarity(repository_id: str) -> Dict[str, Any]:
    """
    Get semantic similarity data for visualization
    
    This would integrate with ChromaDB for real embeddings
    """
    try:
        G = networkx_service.get_graph(repository_id)
        
        if not G:
            raise HTTPException(
                status_code=404,
                detail=f"Graph not found for repository: {repository_id}"
            )
        
        # Mock similarity data - would be replaced with real ChromaDB queries
        file_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "file"]
        
        similarity_matrix = []
        for i, node1 in enumerate(file_nodes[:10]):
            row = []
            for j, node2 in enumerate(file_nodes[:10]):
                # Mock similarity score
                if i == j:
                    score = 1.0
                else:
                    score = 0.3 + (0.4 * ((i + j) % 5) / 5)
                row.append(score)
            similarity_matrix.append(row)
        
        return {
            "repository_id": repository_id,
            "nodes": [G.nodes[n].get("label", n) for n in file_nodes[:10]],
            "similarity_matrix": similarity_matrix,
            "note": "Mock data - integrate with ChromaDB for real embeddings"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting similarity data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Made with Bob
