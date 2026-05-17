from pydantic import BaseModel
from typing import List, Optional


class ChunkMetadata(BaseModel):
    chunk_id: str
    content: str
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class ChromaStoreSummaryRequest(BaseModel):
    repository_id: str
    summary_text: str
    metadata: Optional[dict[str, str]] = None


class ChromaStoreSummaryResponse(BaseModel):
    repository_id: str
    stored: bool
    message: str


class ChromaStoreChunksRequest(BaseModel):
    repository_id: str
    chunks: List[ChunkMetadata]


class ChromaStoreChunksResponse(BaseModel):
    repository_id: str
    stored_count: int
    message: str


class ChromaSearchRequest(BaseModel):
    query: str
    repository_id: Optional[str] = None
    top_k: int = 5


class SearchResultItem(BaseModel):
    chunk_id: str
    score: float
    snippet: str
    file_path: Optional[str] = None


class ChromaSearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]


class ChromaHealthResponse(BaseModel):
    status: str
    detail: str
