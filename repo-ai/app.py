"""
Minimal Flask API for Repository Intelligence Testing (Hackathon MVP).
Wraps existing orchestration without modifying core modules.
"""

from pathlib import Path

from dotenv import load_dotenv

# Load .env before any module reads config (must run before main/config imports)
_APP_ROOT = Path(__file__).resolve().parent
load_dotenv(_APP_ROOT / ".env", override=True)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import tempfile
import zipfile
import sys
import logging

# Import existing orchestration
from main import run_pipeline
import config

# Import integration layer
from integrations.parser_connector import parser_connector
from integrations.repository_uploader import repository_uploader, RepositoryUploadError
from integrations.repository_session import get_session_manager
from integrations.data_validator import get_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Temporary repository storage
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "repo-ai-uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Repository session manager (replaces active_repo dict)
session_manager = get_session_manager()

# Data validator for runtime verification
validator = get_validator(strict_mode=False)  # Warning mode


@app.route('/')
def index():
    """Serve frontend UI."""
    return send_from_directory('frontend', 'index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint with parser-workflow status."""
    config.reload_from_env()
    parser_available = parser_connector.health_check()
    active_session = session_manager.get_active_session()
    _, llm_configured = config.get_active_api_key()

    return jsonify({
        "status": "ready",
        "backend": "operational",
        "llm_provider": config.LLM_PROVIDER,
        "llm_configured": llm_configured,
        "parser_workflow": "available" if parser_available else "unavailable",
        "active_repository": active_session.repository_id if active_session else "none",
        "file_count": active_session.file_count if active_session else 0,
        "parser_indexed": active_session.parser_indexed if active_session else False,
        "parser_ready": active_session.parser_ready if active_session else False,
        "sessions": session_manager.get_summary(),
    })


@app.route('/api/upload-repository', methods=['POST'])
def upload_repository():
    """Upload and extract repository ZIP file, then send to parser-workflow."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    
    if not file.filename.endswith('.zip'):
        return jsonify({"error": "Only ZIP files supported"}), 400
    
    try:
        # Save and extract ZIP locally
        repo_name = file.filename.replace('.zip', '')
        repo_path = UPLOAD_FOLDER / repo_name
        repo_path.mkdir(exist_ok=True)
        
        zip_path = repo_path / file.filename
        file.save(str(zip_path))
        
        logger.info(f"Extracting {file.filename}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(repo_path)
        
        # Scan repository files
        SKIP_DIRS = {
            "node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build",
            "target", ".github", ".vscode", ".idea", "coverage", ".next", "out",
            "bin", "obj", ".gradle", "vendor", "__tests__",
        }
        
        files = []
        for root, dirs, filenames in os.walk(repo_path):
            # Prune directories in-place to avoid traversing them
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            
            for filename in filenames:
                if filename.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h')):
                    rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                    files.append(rel_path)
        
        logger.info(f"Found {len(files)} source files")
        
        # Create NEW repository session (invalidates previous)
        import datetime
        session = session_manager.create_session(
            repository_id=repo_name,
            upload_path=repo_path,
            file_count=len(files),
        )
        
        # Try to send to parser-workflow for indexing
        parser_result = None
        parser_error = None
        
        try:
            logger.info(f"Sending {repo_name} to parser-workflow...")
            parser_result = repository_uploader.upload_repository(
                zip_path=zip_path,
                repository_id=repo_name,
            )
            
            # Wait for processing (with timeout)
            logger.info("Waiting for parser-workflow to process repository...")
            ready = repository_uploader.wait_for_processing(
                repository_id=repo_name,
                timeout=30,
            )
            
            # Update session status
            session.update_parser_status(
                indexed=True,
                ready=ready,
                graph_available=False,
                dependencies_available=False,
            )
            
            # Check if graph and dependencies are available
            if ready:
                try:
                    graph_check = parser_connector.fetch_dependency_graph(repo_name)
                    node_count = len(graph_check.get("nodes", []))
                    edge_count = len(graph_check.get("edges", []))
                    session.update_graph_metrics(node_count, edge_count)
                    logger.info(f"✓ Graph available: {node_count} nodes, {edge_count} edges")
                except Exception as e:
                    logger.warning(f"Graph check failed: {e}")
                
                try:
                    deps_check = parser_connector.fetch_dependencies(repo_name)
                    external_count = len(deps_check.get("external", []))
                    internal_count = len(deps_check.get("internal", []))
                    session.update_dependency_metrics(external_count, internal_count)
                    logger.info(f"✓ Dependencies available: {external_count} external, {internal_count} internal")
                except Exception as e:
                    logger.warning(f"Dependencies check failed: {e}")
            
            logger.info(f"Parser-workflow processing: {'complete' if ready else 'in progress'}")
            
        except RepositoryUploadError as e:
            logger.warning(f"Parser-workflow upload failed: {e}")
            parser_error = str(e)
        except Exception as e:
            logger.warning(f"Unexpected parser error: {e}")
            parser_error = f"Unexpected error: {str(e)}"
        
        response = {
            "success": True,
            "repository": repo_name,
            "file_count": len(files),
            "files": files[:20],  # Return first 20 files
            "parser_workflow": {
                "uploaded": parser_result is not None,
                "indexed": session.parser_indexed,
                "ready": session.parser_ready,
                "graph_available": session.graph_available,
                "dependencies_available": session.dependencies_available,
                "error": parser_error,
            },
            "upload_timestamp": session.upload_timestamp.isoformat(),
            "session": session.get_status(),
        }
        
        if parser_error:
            response["warning"] = (
                "Repository uploaded locally but parser-workflow integration failed. "
                "System will use mock data for queries."
            )
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ask-query', methods=['POST'])
def ask_query():
    """Process repository intelligence query using live or mock data."""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400
    
    try:
        # Get active session
        session = session_manager.get_active_session()
        repo_id = session.repository_id if session else None
        
        # Check if we have a live repository indexed
        using_live_data = (
            session and
            session.parser_indexed and
            session.parser_ready and
            session.graph_available
        )
        
        logger.info("=" * 60)
        logger.info("QUERY PROCESSING START")
        logger.info(f"Repository: {repo_id or 'mock'}")
        logger.info(f"Query: {query}")
        logger.info(f"Using live data: {using_live_data}")
        if session:
            logger.info(f"Parser ready: {session.parser_ready}")
            logger.info(f"Graph available: {session.graph_available} ({session.graph_node_count} nodes)")
            logger.info(f"Dependencies available: {session.dependencies_available}")
            logger.info(f"Session queries: {session.query_count}")
        logger.info("=" * 60)

        config.reload_from_env()
        _, llm_ok = config.get_active_api_key()
        if not llm_ok and not config.USE_MOCK_LLM and config.LLM_PROVIDER != "mock":
            return jsonify({
                "success": False,
                "error": (
                    f"LLM API key not configured for provider '{config.LLM_PROVIDER}'. "
                    "Edit repo-ai/.env (see .env.example), add your key, then restart: python app.py"
                ),
            }), 400

        # Run existing orchestration pipeline
        result = run_pipeline(query, repository_id=repo_id)
        
        logger.info("=" * 60)
        logger.info("QUERY PROCESSING COMPLETE")
        logger.info("=" * 60)
        
        # Record query in session
        if session:
            session.record_query(query, result.get("intent", "unknown"), {
                "data_source": "live" if using_live_data else "mock",
                "validation_passed": result.get("provenance", {}).get("validation", {}).get("is_valid", False),
            })
        
        # Return structured response with data source info
        return jsonify({
            "success": True,
            "query": query,
            "repository": repo_id or "mock",
            "data_source": "live" if using_live_data else "mock",
            "parser_ready": session.parser_ready if session else False,
            "graph_available": session.graph_available if session else False,
            "dependencies_available": session.dependencies_available if session else False,
            "validation": result.get("provenance", {}).get("validation", {}),
            "result": result,
        })
    
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        msg = str(e)
        status = 401 if "Invalid API key" in msg or "401" in msg else 500
        return jsonify({"success": False, "error": msg}), status


@app.route('/api/graph/<repository_id>', methods=['GET'])
def get_graph(repository_id):
    """Fetch dependency graph for visualization."""
    try:
        logger.info(f"Fetching graph for repository: {repository_id}")
        
        # Fetch graph from parser-workflow
        graph_data = parser_connector.fetch_dependency_graph(repository_id)
        
        if not graph_data:
            return jsonify({
                "success": False,
                "error": "Graph not available for this repository"
            }), 404
        
        from integrations.graph_format import normalize_cytoscape_graph

        graph_normalized = normalize_cytoscape_graph(graph_data)
        logger.info(
            f"Graph retrieved: {graph_normalized['node_count']} nodes, "
            f"{graph_normalized['edge_count']} edges"
        )

        return jsonify({
            "success": True,
            "repository": repository_id,
            "graph": graph_normalized,
        })
    
    except Exception as e:
        logger.error(f"Failed to fetch graph: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Repository Intelligence Testing Interface")
    print("="*60)
    print(f"Frontend: http://localhost:5000")
    print(f"API: http://localhost:5000/api/health")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

# Made with Bob
