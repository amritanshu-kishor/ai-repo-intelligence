"""
Repository Upload and Processing Routes
Simplified version that works with ZIP files
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional, List, Dict, Any
import tempfile
import shutil
import zipfile
from pathlib import Path

from networkx_service import networkx_service
from graph_connector import graph_connector
from dependency_extractor import parse_repository
from repository_session_store import repository_session_store
from logger import get_logger

logger = get_logger()

router = APIRouter(tags=["upload"])


@router.post("/upload/repository")
async def upload_repository(
    file: UploadFile = File(...),
    repository_id: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """Upload a repository ZIP file and generate a real dependency graph."""
    filename = file.filename or "repository.zip"

    if not filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")

    if not repository_id:
        repository_id = filename.replace('.zip', '').replace(' ', '-').replace('.', '-')

    logger.info(f"Processing upload for repository: {repository_id}")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / filename

            with open(zip_path, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)

            extract_path = temp_path / "extracted"
            extract_path.mkdir()

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            repo_root = extract_path
            subdirs = [d for d in extract_path.iterdir() if d.is_dir()]
            if len(subdirs) == 1:
                repo_root = subdirs[0]
                logger.info(f"Found wrapper directory: {repo_root.name}")

            logger.info(f"Repository root: {repo_root}")

            parsed_files, dependencies, parse_stats = parse_repository(repo_root)

            if not parsed_files:
                raise HTTPException(status_code=400, detail="No source files found in ZIP")

            repository_session_store.invalidate(repository_id)
            session = repository_session_store.save(
                repository_id,
                parsed_files,
                dependencies,
                external_packages=parse_stats.get("external_packages_list", []),
                parse_stats=parse_stats,
            )

            G = networkx_service.create_graph_from_dependencies(
                repository_id,
                dependencies,
                parsed_files,
            )

            cytoscape_data = networkx_service.to_cytoscape_format(G)
            metrics = networkx_service.calculate_metrics(G)
            cycles = networkx_service.find_circular_dependencies(G)

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

            logger.info(
                f"Successfully processed repository: {repository_id} | "
                f"files={parse_stats.get('files_scanned', 0)} "
                f"imports={parse_stats.get('imports_found', 0)} "
                f"nodes={G.number_of_nodes()} edges={G.number_of_edges()} "
                f"cycles={len(cycles)}"
            )

            return {
                "repository_id": repository_id,
                "status": "success",
                "graph": cytoscape_data,
                "metrics": metrics,
                "files_count": len(parsed_files),
                "dependencies_count": len(dependencies),
                "parse_stats": parse_stats,
                "cycles_detected": len(cycles),
            }

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing repository: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing repository: {str(e)}")


def parse_repository_simple(repo_path: Path) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Backward-compatible wrapper used by repository_service."""
    parsed_files, dependencies, _stats = parse_repository(repo_path)
    return parsed_files, dependencies


@router.get("/upload/test")
async def test_upload_endpoint():
    return {
        "status": "ok",
        "message": "Upload endpoint is working",
        "instructions": "POST a ZIP file to /api/v1/upload/repository",
    }
