from typing import Any, Dict, List

from empty_window_engine import empty_window_engine_registry


class GraphConnector:
    """Routes graph and impact calls to the empty-window NetworkX engine."""

    async def request_repository_graph(self, repository_id: str) -> Dict[str, Any]:
        return empty_window_engine_registry.export_repository_graph(repository_id)

    async def fetch_dependency_graph(self, repository_id: str) -> List[Dict[str, Any]]:
        return empty_window_engine_registry.list_dependencies(repository_id)

    async def submit_change_impact(
        self,
        repository_id: str,
        modified_file_path: str,
        change_description: str,
    ) -> str:
        return empty_window_engine_registry.submit_change_impact(
            repository_id=repository_id,
            modified_file_path=modified_file_path,
            change_description=change_description,
        )

    async def fetch_affected_modules(self, repository_id: str) -> List[Dict[str, str]]:
        return empty_window_engine_registry.get_affected_modules(repository_id)

    async def register_graph(self, repository_id: str, graph_data: Dict[str, Any]) -> None:
        """Called later when parser/upload provides dependency JSON for a repository."""
        empty_window_engine_registry.register_graph(repository_id, graph_data)

    async def check_connection(self) -> str:
        return empty_window_engine_registry.check_connection()


graph_connector = GraphConnector()
