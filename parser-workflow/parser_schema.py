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
