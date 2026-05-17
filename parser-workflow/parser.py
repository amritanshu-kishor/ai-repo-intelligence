from fastapi import APIRouter, HTTPException, status

from parser import (
    ParserStatusResponse,
    ParserTriggerRequest,
    ParserTriggerResponse,
)
from parser_service import parser_service

router = APIRouter(tags=["parser"])


@router.post(
    "/parser/trigger",
    response_model=ParserTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_parser(request: ParserTriggerRequest) -> ParserTriggerResponse:
    return await parser_service.trigger_parse(request.repository_id)


@router.get(
    "/parser/{repository_id}/status",
    response_model=ParserStatusResponse,
)
async def get_parser_status(repository_id: str) -> ParserStatusResponse:
    return await parser_service.get_parse_status(repository_id)
