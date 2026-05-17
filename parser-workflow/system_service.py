from typing import List

from system import ConnectivityStatusResponse, HealthResponse, ServiceStatusResponse
from database_connector import database_connector
from parser_connector import parser_connector
from ai_connector import ai_connector
from graph_connector import graph_connector


class SystemService:
    async def health_check(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            uptime="0s",
            message="System API is available and ready to route requests.",
        )

    async def _safe_check(self, check_coro) -> str:
        try:
            return await check_coro
        except Exception:
            return "unavailable"

    async def get_service_status(self) -> ServiceStatusResponse:
        services: List[dict] = [
            {"name": "database", "status": await self._safe_check(database_connector.check_connection())},
            {"name": "parser", "status": await self._safe_check(parser_connector.check_connection())},
            {"name": "graph", "status": await self._safe_check(graph_connector.check_connection())},
            {"name": "ai", "status": await self._safe_check(ai_connector.check_connection())},
        ]
        return ServiceStatusResponse(
            services=services,
            message="Service status summary returned from system diagnostics placeholder.",
        )

    async def get_connectivity_status(self) -> ConnectivityStatusResponse:
        services: List[dict] = [
            {"name": "database", "connection": await self._safe_check(database_connector.check_connection())},
            {"name": "parser", "connection": await self._safe_check(parser_connector.check_connection())},
            {"name": "graph", "connection": await self._safe_check(graph_connector.check_connection())},
            {"name": "ai", "connection": await self._safe_check(ai_connector.check_connection())},
        ]
        return ConnectivityStatusResponse(
            services=services,
            message="Module connectivity status placeholder.",
        )


system_service = SystemService()
