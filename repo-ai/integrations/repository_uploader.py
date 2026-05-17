"""
Repository Upload Integration - Sends uploaded repositories to parser-workflow for processing.

This module bridges the gap between repo-ai's upload endpoint and parser-workflow's
repository processing pipeline.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


class RepositoryUploadError(Exception):
    """Raised when repository upload to parser-workflow fails."""
    pass


class RepositoryUploader:
    """
    Handles uploading repositories to parser-workflow backend for processing.
    
    Workflow:
    1. User uploads ZIP to repo-ai
    2. repo-ai extracts ZIP locally
    3. RepositoryUploader sends to parser-workflow
    4. parser-workflow processes and indexes
    5. repo-ai can then query the indexed data
    """
    
    def __init__(self, parser_url: str = "http://127.0.0.1:8001"):
        """
        Initialize repository uploader.
        
        Args:
            parser_url: Base URL of parser-workflow backend
        """
        self.parser_url = parser_url.rstrip("/")
        self.session = requests.Session()
    
    def upload_repository(
        self,
        zip_path: str | Path,
        repository_id: str,
    ) -> dict[str, Any]:
        """
        Upload repository ZIP to parser-workflow for processing.
        
        Args:
            zip_path: Path to repository ZIP file
            repository_id: Unique identifier for the repository
            
        Returns:
            Response from parser-workflow containing processing status
            
        Raises:
            RepositoryUploadError: If upload fails
        """
        zip_path = Path(zip_path)
        
        if not zip_path.exists():
            raise RepositoryUploadError(f"ZIP file not found: {zip_path}")
        
        if not zip_path.suffix == ".zip":
            raise RepositoryUploadError(f"File must be a ZIP: {zip_path}")
        
        try:
            # Upload to parser-workflow
            url = f"{self.parser_url}/api/v1/upload/repository"
            
            with open(zip_path, "rb") as f:
                files = {"file": (zip_path.name, f, "application/zip")}
                data = {"repository_id": repository_id}
                
                logger.info(f"Uploading {zip_path.name} to parser-workflow...")
                
                response = self.session.post(
                    url,
                    files=files,
                    data=data,
                    timeout=120,  # 2 minutes for large repos
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(
                    f"Repository uploaded successfully: {repository_id} "
                    f"({result.get('file_count', 0)} files)"
                )
                
                return result
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to parser-workflow: {e}")
            raise RepositoryUploadError(
                f"Parser-workflow backend unavailable at {self.parser_url}. "
                "Ensure it's running on port 8001."
            ) from e
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Upload timeout: {e}")
            raise RepositoryUploadError(
                "Repository upload timed out. File may be too large."
            ) from e
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Upload failed: {e}")
            status = e.response.status_code if e.response else "unknown"
            text = e.response.text if e.response else str(e)
            raise RepositoryUploadError(
                f"Parser-workflow upload failed: {status} - {text}"
            ) from e
            
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            raise RepositoryUploadError(f"Upload failed: {e}") from e
    
    def check_repository_status(self, repository_id: str) -> dict[str, Any]:
        """
        Check processing status of uploaded repository.
        
        Args:
            repository_id: Repository identifier
            
        Returns:
            Status information including:
            - indexed: bool
            - file_count: int
            - graph_generated: bool
            - ready: bool
        """
        try:
            url = f"{self.parser_url}/api/v1/repository/{repository_id}/status"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.warning(f"Failed to check repository status: {e}")
            return {
                "indexed": False,
                "ready": False,
                "error": str(e),
            }
    
    def wait_for_processing(
        self,
        repository_id: str,
        timeout: int = 60,
        poll_interval: int = 2,
    ) -> bool:
        """
        Wait for repository to be fully processed.
        
        Args:
            repository_id: Repository identifier
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks
            
        Returns:
            True if processing completed, False if timeout
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.check_repository_status(repository_id)
            
            if status.get("ready"):
                logger.info(f"Repository {repository_id} is ready")
                return True
            
            if status.get("error"):
                logger.error(f"Repository processing failed: {status['error']}")
                return False
            
            time.sleep(poll_interval)
        
        logger.warning(f"Repository processing timeout after {timeout}s")
        return False


# Singleton instance
repository_uploader = RepositoryUploader()

# Made with Bob
