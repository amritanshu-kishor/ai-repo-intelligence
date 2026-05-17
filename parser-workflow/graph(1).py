from typing import Any, Dict, List

from pydantic import BaseModel


class GraphResponse(BaseModel):
    repository_id: str
    graph: Dict[str, Any]
    summary: str


class DependencyGraphResponse(BaseModel):
    repository_id: str
    dependencies: List[Dict[str, Any]]
    details: str
