from chromadb_connector import chromadb_connector
from chroma_schema import (
    ChromaHealthResponse,
    ChromaSearchRequest,
    ChromaSearchResponse,
    ChromaStoreChunksRequest,
    ChromaStoreChunksResponse,
    ChromaStoreSummaryRequest,
    ChromaStoreSummaryResponse,
)


class ChromaService:
    async def store_summary(self, request: ChromaStoreSummaryRequest) -> ChromaStoreSummaryResponse:
        stored = await chromadb_connector.store_repository_summary(
            repository_id=request.repository_id,
            summary_text=request.summary_text,
            metadata=request.metadata,
        )

        return ChromaStoreSummaryResponse(
            repository_id=request.repository_id,
            stored=stored,
            message="Summary request forwarded to ChromaDB connector." if stored else "ChromaDB connector placeholder did not store summary.",
        )

    async def store_chunks(self, request: ChromaStoreChunksRequest) -> ChromaStoreChunksResponse:
        stored_count = await chromadb_connector.store_chunks(
            repository_id=request.repository_id,
            chunks=request.chunks,
        )
        return ChromaStoreChunksResponse(
            repository_id=request.repository_id,
            stored_count=stored_count,
            message="Repository chunks have been forwarded to the ChromaDB connector.",
        )

    async def semantic_search(self, request: ChromaSearchRequest) -> ChromaSearchResponse:
        results = await chromadb_connector.semantic_search(
            query=request.query,
            repository_id=request.repository_id,
            top_k=request.top_k,
        )
        return ChromaSearchResponse(query=request.query, results=results)

    async def health_check(self) -> ChromaHealthResponse:
        status = await chromadb_connector.check_health()
        return ChromaHealthResponse(
            status=status,
            detail="ChromaDB connector is reachable via placeholder health check.",
        )


chroma_service = ChromaService()
