from impact import (
    AffectedModulesResponse,
    ChangeImpactRequest,
    ChangeImpactResponse,
)
from graph_connector import graph_connector


class ImpactService:
    async def submit_change_path(self, request: ChangeImpactRequest) -> ChangeImpactResponse:
        impact_request_id = await graph_connector.submit_change_impact(
            repository_id=request.repository_id,
            modified_file_path=request.modified_file_path,
            change_description=request.change_description,
        )
        return ChangeImpactResponse(
            repository_id=request.repository_id,
            modified_file_path=request.modified_file_path,
            impact_request_id=impact_request_id,
            status="queued",
            message="Change impact request has been forwarded to the impact analysis module.",
        )

    async def get_affected_modules(self, repository_id: str) -> AffectedModulesResponse:
        modules = await graph_connector.fetch_affected_modules(repository_id)
        return AffectedModulesResponse(
            repository_id=repository_id,
            affected_modules=modules,
            summary=f"Found {len(modules)} affected module(s) via empty-window impact analysis.",
        )


impact_service = ImpactService()
