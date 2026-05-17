from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    API_TITLE: str = "Repository Intelligence API"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = (
        "FastAPI backend for repository intelligence. "
        "Graph and impact analysis are powered by the empty-window NetworkX engine."
    )
    TEMP_REPOSITORY_DIR: str = "./tmp/repositories"
    # 127.0.0.1 avoids some Windows firewall blocks
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8001
    TREESITTER_SERVICE_URL: str = "http://127.0.0.1:9000"
    CHROMADB_SERVICE_URL: str = "http://127.0.0.1:8000"
    # Empty window engine removed during cleanup - not needed for core functionality
    EMPTY_WINDOW_ENGINE_ROOT: str = ""


settings = Settings()

API_TITLE = settings.API_TITLE
API_VERSION = settings.API_VERSION
API_DESCRIPTION = settings.API_DESCRIPTION
TEMP_REPOSITORY_DIR = settings.TEMP_REPOSITORY_DIR
API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
EMPTY_WINDOW_ENGINE_ROOT = settings.EMPTY_WINDOW_ENGINE_ROOT
