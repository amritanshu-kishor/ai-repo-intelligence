from fastapi import APIRouter, File, HTTPException, UploadFile, status

from repository_schema import RepositoryUploadResponse
from repository_service import repository_service

router = APIRouter(tags=["repository"])


@router.post(
    "/repository/upload",
    response_model=RepositoryUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_repository(file: UploadFile = File(...)) -> RepositoryUploadResponse:
    if file.content_type != "application/zip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP repository uploads are supported.",
        )

    return await repository_service.upload_repository(file)


@router.get("/repository/{repository_id}/status")
async def get_repository_status(repository_id: str) -> dict:
    """Processing status for repo-ai upload polling."""
    return await repository_service.get_repository_status(repository_id)
