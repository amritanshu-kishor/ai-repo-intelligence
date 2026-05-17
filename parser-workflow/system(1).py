from typing import Dict, List

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    uptime: str
    message: str


class ServiceStatusResponse(BaseModel):
    services: List[Dict[str, str]]
    message: str


class ConnectivityStatusResponse(BaseModel):
    services: List[Dict[str, str]]
    message: str
