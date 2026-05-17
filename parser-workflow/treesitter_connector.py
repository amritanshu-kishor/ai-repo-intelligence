from typing import Any

from repository_session_store import repository_session_store
from logger import get_logger

logger = get_logger()


class TreeSitterConnector:
    """Returns real dependency metadata from parsed repository sessions."""

    async def submit_repository_for_parsing(self, repository_id: str) -> None:
        return None

    async def fetch_parse_status(self, repository_id: str) -> str:
        session = repository_session_store.get(repository_id)
        return "completed" if session else "pending"

    async def get_dependencies(self, repository_id: str) -> list[dict[str, Any]]:
        session = repository_session_store.get(repository_id)
        if not session:
            logger.warning(f"No session for repository: {repository_id}")
            return []

        dependencies: list[dict[str, Any]] = []

        for dep in session.dependencies:
            dep_type = "internal" if dep.get("resolved") and not dep.get("external") else "external"
            dependencies.append({
                "type": dep_type,
                "name": dep.get("to", ""),
                "file_path": dep.get("from", ""),
                "line_number": dep.get("line") or 0,
                "details": dep.get("type", "imports"),
            })

        for pkg in session.external_packages:
            dependencies.append({
                "type": "package",
                "name": pkg.get("name", ""),
                "file_path": "",
                "line_number": 0,
                "details": "config",
            })

        logger.info(
            f"Returning {len(dependencies)} real dependencies for {repository_id}"
        )
        return dependencies

    async def check_health(self) -> str:
        return "available"


treesitter_connector = TreeSitterConnector()
