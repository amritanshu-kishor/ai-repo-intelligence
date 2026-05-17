from fastapi import APIRouter

from system import (
    ConnectivityStatusResponse,
    HealthResponse,
    ServiceStatusResponse,
)
from system_service import system_service

router = APIRouter(prefix="/system", tags=["system"])


@router.get(
    "/health",
    response_model=HealthResponse,
)
async def health_check() -> HealthResponse:
    return await system_service.health_check()


@router.get(
    "/status",
    response_model=ServiceStatusResponse,
)
async def service_status() -> ServiceStatusResponse:
    return await system_service.get_service_status()


@router.get(
    "/connectivity",
    response_model=ConnectivityStatusResponse,
)
async def connectivity_status() -> ConnectivityStatusResponse:
    return await system_service.get_connectivity_status()
