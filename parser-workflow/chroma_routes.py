from fastapi import APIRouter, status

from chroma_schema import (
    ChromaHealthResponse,
    ChromaSearchRequest,
    ChromaSearchResponse,
    ChromaStoreChunksRequest,
    ChromaStoreChunksResponse,
    ChromaStoreSummaryRequest,
    ChromaStoreSummaryResponse,
)
from chroma_service import chroma_service

router = APIRouter(tags=["chroma"])


@router.post(
    "/chroma/store-summary",
    response_model=ChromaStoreSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def store_summary(request: ChromaStoreSummaryRequest) -> ChromaStoreSummaryResponse:
    return await chroma_service.store_summary(request)


@router.post(
    "/chroma/store-chunks",
    response_model=ChromaStoreChunksResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def store_chunks(request: ChromaStoreChunksRequest) -> ChromaStoreChunksResponse:
    return await chroma_service.store_chunks(request)


@router.post(
    "/chroma/search",
    response_model=ChromaSearchResponse,
)
async def semantic_search(request: ChromaSearchRequest) -> ChromaSearchResponse:
    return await chroma_service.semantic_search(request)


@router.get(
    "/chroma/health",
    response_model=ChromaHealthResponse,
)
async def chroma_health() -> ChromaHealthResponse:
    return await chroma_service.health_check()
