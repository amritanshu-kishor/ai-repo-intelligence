from fastapi import APIRouter

from impact import (
    AffectedModulesResponse,
    ChangeImpactRequest,
    ChangeImpactResponse,
)
from impact_service import impact_service

router = APIRouter(tags=["impact"])


@router.post(
    "/impact/submit",
    response_model=ChangeImpactResponse,
)
async def submit_change_impact(request: ChangeImpactRequest) -> ChangeImpactResponse:
    return await impact_service.submit_change_path(request)


@router.get(
    "/impact/{repository_id}/affected",
    response_model=AffectedModulesResponse,
)
async def get_affected_modules(repository_id: str) -> AffectedModulesResponse:
    return await impact_service.get_affected_modules(repository_id)
