from fastapi import APIRouter, HTTPException

from graph import GraphResponse, DependencyGraphResponse
from graph_service import graph_service

router = APIRouter(tags=["graph"])


@router.get(
    "/graph/{repository_id}",
    response_model=GraphResponse,
)
async def get_repository_graph(repository_id: str) -> GraphResponse:
    return await graph_service.generate_graph(repository_id)


@router.get(
    "/graph/{repository_id}/dependencies",
    response_model=DependencyGraphResponse,
)
async def get_dependency_graph(repository_id: str) -> DependencyGraphResponse:
    return await graph_service.get_dependency_graph(repository_id)
