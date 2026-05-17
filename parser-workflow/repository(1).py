from typing import List

from pydantic import BaseModel


class RepositorySummary(BaseModel):
    repository_id: str
    name: str
    status: str
    upload_timestamp: str


class RepositoryUploadResponse(BaseModel):
    repository_id: str
    name: str
    status: str
    message: str


class RepositoryStatusResponse(BaseModel):
    repository_id: str
    name: str
    status: str
    details: str


class RepositoryListResponse(BaseModel):
    repositories: List[RepositorySummary]
