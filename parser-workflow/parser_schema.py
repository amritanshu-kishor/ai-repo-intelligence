from pydantic import BaseModel
from typing import List, Optional


class ParserTriggerRequest(BaseModel):
    repository_id: str


class ParserTriggerResponse(BaseModel):
    repository_id: str
    status: str
    message: str


class ParserStatusResponse(BaseModel):
    repository_id: str
    status: str
    progress: str
    details: str


class DependencyItem(BaseModel):
    type: str
    name: str
    file_path: str
    line_number: int
    details: Optional[str] = None


class ParserDependenciesResponse(BaseModel):
    repository_id: str
    dependencies: List[DependencyItem]
    message: str


class SummaryItem(BaseModel):
    path: str
    summary: str
    symbols: List[str] = []
    language: Optional[str] = None
    loc: Optional[int] = None


class ParserSummariesResponse(BaseModel):
    repository_id: str
    generated_at: str
    items: List[SummaryItem]
    file_count: int
    message: str
