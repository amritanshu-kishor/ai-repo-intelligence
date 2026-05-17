"""
In-memory store for parsed repository sessions.
Invalidates previous session data when the same repository_id is re-uploaded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from logger import get_logger

logger = get_logger()


@dataclass
class RepositorySession:
    repository_id: str
    parsed_files: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    external_packages: list[dict[str, Any]] = field(default_factory=list)
    parse_stats: dict[str, Any] = field(default_factory=dict)


class RepositorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, RepositorySession] = {}

    def invalidate(self, repository_id: str) -> None:
        if repository_id in self._sessions:
            logger.info(f"Invalidating previous session for repository: {repository_id}")
            del self._sessions[repository_id]

    def save(
        self,
        repository_id: str,
        parsed_files: list[dict[str, Any]],
        dependencies: list[dict[str, Any]],
        external_packages: list[dict[str, Any]] | None = None,
        parse_stats: dict[str, Any] | None = None,
    ) -> RepositorySession:
        self.invalidate(repository_id)
        session = RepositorySession(
            repository_id=repository_id,
            parsed_files=parsed_files,
            dependencies=dependencies,
            external_packages=external_packages or [],
            parse_stats=parse_stats or {},
        )
        self._sessions[repository_id] = session
        logger.info(
            f"Session saved for {repository_id}: "
            f"{len(parsed_files)} files, {len(dependencies)} deps"
        )
        return session

    def get(self, repository_id: str) -> RepositorySession | None:
        return self._sessions.get(repository_id)

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())


repository_session_store = RepositorySessionStore()
