from graph import DependencyGraphResponse, GraphResponse
from graph_connector import graph_connector


class GraphService:
    async def generate_graph(self, repository_id: str) -> GraphResponse:
        graph_payload = await graph_connector.request_repository_graph(repository_id)
        return GraphResponse(
            repository_id=repository_id,
            graph=graph_payload,
            summary=(
                f"Dependency graph from empty-window engine "
                f"({graph_payload.get('node_count', 0)} nodes, "
                f"{graph_payload.get('edge_count', 0)} edges)."
            ),
        )

    async def get_dependency_graph(self, repository_id: str) -> DependencyGraphResponse:
        dependencies = await graph_connector.fetch_dependency_graph(repository_id)
        return DependencyGraphResponse(
            repository_id=repository_id,
            dependencies=dependencies,
            details=f"Returned {len(dependencies)} dependency edges from empty-window engine.",
        )


graph_service = GraphService()
