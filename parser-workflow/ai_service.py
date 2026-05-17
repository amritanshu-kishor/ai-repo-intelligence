from ai import (
    AIResponseStatusResponse,
    AskQuestionRequest,
    AskQuestionResponse,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
)
from ai_connector import ai_connector


class AIService:
    async def ask_question(self, request: AskQuestionRequest) -> AskQuestionResponse:
        request_id = await ai_connector.submit_question(
            repository_id=request.repository_id,
            question=request.question,
        )
        return AskQuestionResponse(
            request_id=request_id,
            repository_id=request.repository_id,
            status="queued",
            answer="Answer generation is pending from the AI module.",
        )

    async def request_impact_analysis(self, request: ImpactAnalysisRequest) -> ImpactAnalysisResponse:
        request_id = await ai_connector.submit_impact_request(
            repository_id=request.repository_id,
            target_component=request.target_component,
            context=request.context,
        )
        return ImpactAnalysisResponse(
            request_id=request_id,
            repository_id=request.repository_id,
            status="queued",
            impact_summary="Impact analysis request has been forwarded to the AI service.",
        )

    async def get_ai_response(self, request_id: str) -> AIResponseStatusResponse:
        result = await ai_connector.fetch_response(request_id)
        return AIResponseStatusResponse(
            request_id=request_id,
            repository_id=result.get("repository_id", ""),
            status=result.get("status", "processing"),
            result=result.get("result", "AI response placeholder."),
        )

ai_service = AIService()
