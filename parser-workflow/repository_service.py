from fastapi import UploadFile
import tempfile
import shutil
import zipfile
from pathlib import Path

from repository_schema import RepositoryUploadResponse
from file_handler import save_repository_upload
from networkx_service import networkx_service
from graph_connector import graph_connector
from dependency_extractor import parse_repository
from repository_session_store import repository_session_store
from logger import get_logger

logger = get_logger()


class RepositoryService:
    async def upload_repository(self, file: UploadFile) -> RepositoryUploadResponse:
        """
        Upload repository and build dependency graph
        
        This now performs the complete workflow:
        1. Save and extract ZIP
        2. Parse repository files
        3. Build NetworkX graph
        4. Register graph with empty_window_engine
        5. Return graph data
        """
        repository_id, stored_path = await save_repository_upload(file)
        filename = file.filename or "repository.zip"
        
        logger.info(f"🔄 Building graph for repository: {repository_id}")
        
        try:
            # Extract and parse the uploaded ZIP
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_path = Path(stored_path)
                
                # Extract ZIP
                extract_path = temp_path / "extracted"
                extract_path.mkdir()
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Find repo root (handle GitHub ZIP wrapper)
                repo_root = extract_path
                subdirs = [d for d in extract_path.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    repo_root = subdirs[0]
                    logger.info(f"Found wrapper directory: {repo_root.name}")
                
                repository_session_store.invalidate(repository_id)
                parsed_files, dependencies, parse_stats = parse_repository(repo_root)
                repository_session_store.save(
                    repository_id, parsed_files, dependencies,
                    parse_stats=parse_stats,
                )
                
                if not parsed_files:
                    logger.warning(f"⚠️  No source files found in {repository_id}")
                    # Return empty graph structure
                    return RepositoryUploadResponse(
                        repository_id=repository_id,
                        file_name=filename,
                        stored_path=stored_path,
                        status="uploaded",
                        message=f"Repository uploaded but no source files found. Files: 0, Dependencies: 0",
                    )
                
                # Create NetworkX graph
                G = networkx_service.create_graph_from_dependencies(
                    repository_id,
                    dependencies,
                    parsed_files
                )
                
                # Convert to Cytoscape format
                cytoscape_data = networkx_service.to_cytoscape_format(G)
                
                # Register graph with empty_window_engine for graph_connector access
                graph_data = {
                    "nodes": [
                        elem["data"]
                        for elem in cytoscape_data["elements"]
                        if "source" not in elem["data"]
                    ],
                    "edges": [
                        elem["data"]
                        for elem in cytoscape_data["elements"]
                        if "source" in elem["data"]
                    ],
                }
                await graph_connector.register_graph(repository_id, graph_data)
                
                # Enhanced logging for edge debugging
                internal_edges = sum(1 for d in dependencies if d.get("resolved", False))
                external_edges = sum(1 for d in dependencies if d.get("external", False))
                logger.info(f"✅ Graph built for {repository_id}:")
                logger.info(f"   📊 Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
                logger.info(f"   🔗 Internal edges: {internal_edges}, External edges: {external_edges}")
                logger.info(f"   📦 Registered {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
                
                # Log sample edges for verification
                if graph_data['edges']:
                    sample_edges = graph_data['edges'][:3]
                    logger.info(f"   🔍 Sample edges: {sample_edges}")
                else:
                    logger.warning(f"   ⚠️  NO EDGES in graph_data! Dependencies count: {len(dependencies)}")
                
                return RepositoryUploadResponse(
                    repository_id=repository_id,
                    file_name=filename,
                    stored_path=stored_path,
                    status="uploaded",
                    message=f"Repository uploaded and graph built. Files: {len(parsed_files)}, Dependencies: {len(dependencies)}, Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}",
                )
                
        except Exception as e:
            logger.error(f"❌ Error building graph for {repository_id}: {e}", exc_info=True)
            return RepositoryUploadResponse(
                repository_id=repository_id,
                file_name=filename,
                stored_path=stored_path,
                status="uploaded",
                message=f"Repository uploaded but graph build failed: {str(e)}",
            )
    
    async def get_repository_status(self, repository_id: str) -> dict:
        from repository_session_store import repository_session_store
        session = repository_session_store.get(repository_id)
        G = networkx_service.get_graph(repository_id)
        return {
            "repository_id": repository_id,
            "indexed": session is not None,
            "ready": G is not None and G.number_of_nodes() > 0,
            "graph_generated": G is not None,
            "file_count": len(session.parsed_files) if session else 0,
            "node_count": G.number_of_nodes() if G else 0,
            "edge_count": G.number_of_edges() if G else 0,
        }


repository_service = RepositoryService()
