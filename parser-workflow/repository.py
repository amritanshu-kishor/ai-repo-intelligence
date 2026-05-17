from fastapi import APIRouter, File, HTTPException, UploadFile, status

from repository import (
    RepositoryListResponse,
    RepositoryStatusResponse,
    RepositoryUploadResponse,
)
from repository_service import repository_service
from file_upload import save_upload_file

router = APIRouter(tags=["repository"])


@router.post(
    "/repositories/upload",
    response_model=RepositoryUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_repository(file: UploadFile = File(...)) -> RepositoryUploadResponse:
    if file.content_type != "application/zip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP archives are supported for repository upload.",
        )

    file_path = await save_upload_file(file)
    result = await repository_service.upload_repository(file_path, file.filename)
    return result


@router.get(
    "/repositories/{repository_id}/status",
    response_model=RepositoryStatusResponse,
)
async def get_repository_status(repository_id: str) -> RepositoryStatusResponse:
    return await repository_service.get_repository_status(repository_id)


@router.get(
    "/repositories",
    response_model=RepositoryListResponse,
)
async def list_repositories() -> RepositoryListResponse:
    return await repository_service.list_repositories()
