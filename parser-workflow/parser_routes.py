from fastapi import APIRouter, status

from parser_schema import (
    ParserDependenciesResponse,
    ParserStatusResponse,
    ParserTriggerRequest,
    ParserTriggerResponse,
)
from parser_service import parser_service

router = APIRouter(tags=["parser"])


@router.post(
    "/parser/parse",
    response_model=ParserTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_parse(request: ParserTriggerRequest) -> ParserTriggerResponse:
    return await parser_service.trigger_parse(request.repository_id)


@router.get(
    "/parser/status/{repo_id}",
    response_model=ParserStatusResponse,
)
async def get_parse_status(repo_id: str) -> ParserStatusResponse:
    return await parser_service.get_parse_status(repo_id)


@router.get(
    "/parser/dependencies/{repo_id}",
    response_model=ParserDependenciesResponse,
)
async def get_dependencies(repo_id: str) -> ParserDependenciesResponse:
    return await parser_service.get_dependencies(repo_id)
