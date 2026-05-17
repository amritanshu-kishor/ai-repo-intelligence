from pydantic import BaseModel


class RepositoryUploadResponse(BaseModel):
    repository_id: str
    file_name: str
    stored_path: str
    status: str
    message: str
