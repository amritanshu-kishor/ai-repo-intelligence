from treesitter_connector import treesitter_connector
from repository_session_store import repository_session_store
from parser_schema import (
    ParserDependenciesResponse,
    ParserStatusResponse,
    ParserSummariesResponse,
    ParserTriggerResponse,
    SummaryItem,
)
from summary_builder import build_repository_summaries


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

    async def get_summaries(self, repository_id: str) -> ParserSummariesResponse:
        session = repository_session_store.get(repository_id)
        if not session or not session.parsed_files:
            return ParserSummariesResponse(
                repository_id=repository_id,
                generated_at="",
                items=[],
                file_count=0,
                message="No parsed session found. Upload repository first.",
            )

        payload = build_repository_summaries(repository_id, session.parsed_files)
        items = [SummaryItem(**item) for item in payload["items"]]
        return ParserSummariesResponse(
            repository_id=repository_id,
            generated_at=payload["generated_at"],
            items=items,
            file_count=payload["file_count"],
            message=f"Generated summaries for {len(items)} file(s) from parsed repository.",
        )


parser_service = ParserService()
