from typing import List

from pydantic import BaseModel


class ChangeImpactRequest(BaseModel):
    repository_id: str
    modified_file_path: str
    change_description: str


class ChangeImpactResponse(BaseModel):
    repository_id: str
    modified_file_path: str
    impact_request_id: str
    status: str
    message: str


class AffectedModule(BaseModel):
    module_name: str
    module_path: str
    reason: str


class AffectedModulesResponse(BaseModel):
    repository_id: str
    affected_modules: List[AffectedModule]
    summary: str
