from typing import AsyncIterator


class DatabaseClient:
    def __init__(self) -> None:
        self.connection = None
        # TODO: Wire this placeholder to a real database or metadata store.

    async def connect(self) -> None:
        """Placeholder for database connection startup."""
        self.connection = None

    async def disconnect(self) -> None:
        """Placeholder for database connection shutdown."""
        self.connection = None

    async def get_connection(self) -> None:
        """Return the active connection placeholder."""
        return self.connection


db_client = DatabaseClient()


async def get_db() -> AsyncIterator[DatabaseClient]:
    """FastAPI dependency injection placeholder for database access."""
    yield db_client
