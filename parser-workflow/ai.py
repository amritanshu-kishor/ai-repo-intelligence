from fastapi import APIRouter

from ai import (
    AIResponseStatusResponse,
    AskQuestionRequest,
    AskQuestionResponse,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
)
from ai_service import ai_service

router = APIRouter(tags=["ai"])


@router.post(
    "/ai/question",
    response_model=AskQuestionResponse,
)
async def ask_repository_question(request: AskQuestionRequest) -> AskQuestionResponse:
    return await ai_service.ask_question(request)


@router.post(
    "/ai/impact",
    response_model=ImpactAnalysisResponse,
)
async def request_impact_analysis(request: ImpactAnalysisRequest) -> ImpactAnalysisResponse:
    return await ai_service.request_impact_analysis(request)


@router.get(
    "/ai/{request_id}",
    response_model=AIResponseStatusResponse,
)
async def get_ai_response(request_id: str) -> AIResponseStatusResponse:
    return await ai_service.get_ai_response(request_id)
