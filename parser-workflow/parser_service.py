from treesitter_connector import treesitter_connector
from repository_session_store import repository_session_store
from parser_schema import (
    ParserDependenciesResponse,
    ParserStatusResponse,
    ParserTriggerResponse,
)


class ParserService:
    async def trigger_parse(self, repository_id: str) -> ParserTriggerResponse:
        await treesitter_connector.submit_repository_for_parsing(repository_id)
        return ParserTriggerResponse(
            repository_id=repository_id,
            status="parsing_queued",
            message="Repository parsing requested.",
        )

    async def get_parse_status(self, repository_id: str) -> ParserStatusResponse:
        session = repository_session_store.get(repository_id)
        if session:
            stats = session.parse_stats
            return ParserStatusResponse(
                repository_id=repository_id,
                status="completed",
                progress="100%",
                details=(
                    f"Parsed {stats.get('files_scanned', 0)} files, "
                    f"{stats.get('resolved_edges', 0)} dependency edges."
                ),
            )
        status = await treesitter_connector.fetch_parse_status(repository_id)
        return ParserStatusResponse(
            repository_id=repository_id,
            status=status,
            progress="0%",
            details="Upload repository to begin parsing.",
        )

    async def get_dependencies(self, repository_id: str) -> ParserDependenciesResponse:
        dependencies = await treesitter_connector.get_dependencies(repository_id)
        session = repository_session_store.get(repository_id)
        msg = (
            f"Real dependencies from uploaded repository ({len(dependencies)} items)."
            if session
            else "No parsed session found. Upload repository first."
        )
        return ParserDependenciesResponse(
            repository_id=repository_id,
            dependencies=dependencies,
            message=msg,
        )


parser_service = ParserService()
