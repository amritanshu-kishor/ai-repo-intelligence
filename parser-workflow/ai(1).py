from pydantic import BaseModel


class AskQuestionRequest(BaseModel):
    repository_id: str
    question: str


class AskQuestionResponse(BaseModel):
    request_id: str
    repository_id: str
    status: str
    answer: str


class ImpactAnalysisRequest(BaseModel):
    repository_id: str
    target_component: str
    context: str


class ImpactAnalysisResponse(BaseModel):
    request_id: str
    repository_id: str
    status: str
    impact_summary: str


class AIResponseStatusResponse(BaseModel):
    request_id: str
    repository_id: str
    status: str
    result: str
