from pydantic import BaseModel


class ParserTriggerRequest(BaseModel):
    repository_id: str


class ParserTriggerResponse(BaseModel):
    repository_id: str
    status: str
    message: str


class ParserStatusResponse(BaseModel):
    repository_id: str
    status: str
    progress: str
    details: str
