"""
Central configuration for the AI orchestration layer.
Environment-driven — no repository-specific values.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

MOCK_DATA_DIR = ROOT_DIR / "mock_data"
PROMPTS_DIR = ROOT_DIR / "prompts"

# --- LLM provider selection (API replacement point) ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface")  # huggingface | watsonx | mock

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
# Router OpenAI-compatible endpoint (replaces deprecated api-inference.huggingface.co)
HF_INFERENCE_URL = os.getenv(
    "HF_INFERENCE_URL",
    "https://router.huggingface.co/v1/chat/completions",
)

# IBM watsonx (API replacement point)
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

# --- Mock data mode for testing (set to false to use live parser-workflow data) ---
# Default is false - system will try live data first, fall back to mock if unavailable
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# --- Backend teammate APIs (integration points) ---
# Parser-workflow backend (local development default)
PARSER_WORKFLOW_URL = os.getenv("PARSER_WORKFLOW_URL", "http://127.0.0.1:8001")

# Legacy API URLs (for future separate services)
PARSER_API_URL = os.getenv("PARSER_API_URL", PARSER_WORKFLOW_URL)
GRAPH_API_URL = os.getenv("GRAPH_API_URL", PARSER_WORKFLOW_URL)
VECTOR_API_URL = os.getenv("VECTOR_API_URL", "")
GRAPH_DB_URL = os.getenv("GRAPH_DB_URL", "")

# Repository scope passed at runtime (not hardcoded in modules)
DEFAULT_REPOSITORY_ID = os.getenv("REPOSITORY_ID", "")
