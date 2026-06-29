"""
Central configuration for the AI orchestration layer.
Environment-driven — no repository-specific values.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
_ENV_PATH = ROOT_DIR / ".env"

MOCK_DATA_DIR = ROOT_DIR / "mock_data"
PROMPTS_DIR = ROOT_DIR / "prompts"

_PLACEHOLDER_MARKERS = ("your_", "_here", "changeme", "xxx", "paste_")


def _env(name: str, default: str = "") -> str:
    """Read env var, strip whitespace and surrounding quotes."""
    raw = os.getenv(name, default)
    if raw is None:
        return ""
    return str(raw).strip().strip('"').strip("'")


def _is_placeholder(value: str) -> bool:
    if not value:
        return True
    lower = value.lower()
    return any(m in lower for m in _PLACEHOLDER_MARKERS)


def reload_from_env() -> None:
    """Reload .env from disk (call after editing keys without restarting)."""
    load_dotenv(_ENV_PATH, override=True)

    global LLM_PROVIDER, LLM_MAX_TOKENS, LLM_TEMPERATURE, LLM_SYSTEM_PROMPT
    global USE_MOCK_LLM, GROQ_API_KEY, GROQ_MODEL, GROQ_API_URL
    global GEMINI_API_KEY, GEMINI_MODEL
    global OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_API_URL
    global HF_API_TOKEN, HF_MODEL, HF_INFERENCE_URL
    global WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_MODEL_ID, WATSONX_URL
    global USE_MOCK_DATA, PARSER_WORKFLOW_URL, PARSER_API_URL, GRAPH_API_URL
    global VECTOR_API_URL, GRAPH_DB_URL, DEFAULT_REPOSITORY_ID

    LLM_PROVIDER = _env("LLM_PROVIDER", "groq").lower()
    LLM_MAX_TOKENS = int(_env("LLM_MAX_TOKENS", "4096"))
    LLM_TEMPERATURE = float(_env("LLM_TEMPERATURE", "0.2"))
    LLM_SYSTEM_PROMPT = _env(
        "LLM_SYSTEM_PROMPT",
        "You are an expert software architect and repository analyst. "
        "Your primary job is to DIRECTLY ANSWER the user's specific question or scenario — "
        "do not deflect into generic architectural overviews unless that is what was asked. "
        "When the user asks about removing, replacing, or changing a specific file, "
        "reason through the exact impact on dependents from the provided graph and dependency data. "
        "Cite actual file paths from the context. Use markdown sections. "
        "Never invent files or dependencies that are not in the provided data.",
    )
    USE_MOCK_LLM = _env("USE_MOCK_LLM", "false").lower() == "true"

    GROQ_API_KEY = _env("GROQ_API_KEY")
    GROQ_MODEL = _env("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_API_URL = _env("GROQ_API_URL", "https://api.groq.com/openai/v1")

    GEMINI_API_KEY = _env("GEMINI_API_KEY")
    GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-2.0-flash")

    OPENROUTER_API_KEY = _env("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = _env("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    OPENROUTER_API_URL = _env("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")

    HF_API_TOKEN = _env("HF_API_TOKEN")
    HF_MODEL = _env("HF_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
    HF_INFERENCE_URL = _env(
        "HF_INFERENCE_URL",
        "https://router.huggingface.co/v1/chat/completions",
    )

    WATSONX_API_KEY = _env("WATSONX_API_KEY")
    WATSONX_PROJECT_ID = _env("WATSONX_PROJECT_ID")
    WATSONX_MODEL_ID = _env("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2")
    WATSONX_URL = _env("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    USE_MOCK_DATA = _env("USE_MOCK_DATA", "false").lower() == "true"
    PARSER_WORKFLOW_URL = _env("PARSER_WORKFLOW_URL", "http://127.0.0.1:8001")
    PARSER_API_URL = _env("PARSER_API_URL", PARSER_WORKFLOW_URL)
    GRAPH_API_URL = _env("GRAPH_API_URL", PARSER_WORKFLOW_URL)
    VECTOR_API_URL = _env("VECTOR_API_URL")
    GRAPH_DB_URL = _env("GRAPH_DB_URL")
    DEFAULT_REPOSITORY_ID = _env("REPOSITORY_ID")


def get_active_api_key() -> tuple[str, bool]:
    """Return (api_key, is_configured) for the selected LLM_PROVIDER."""
    provider = LLM_PROVIDER
    if provider == "mock" or USE_MOCK_LLM:
        return "", True
    if provider == "groq":
        return GROQ_API_KEY, bool(GROQ_API_KEY) and not _is_placeholder(GROQ_API_KEY)
    if provider == "gemini":
        return GEMINI_API_KEY, bool(GEMINI_API_KEY) and not _is_placeholder(GEMINI_API_KEY)
    if provider == "openrouter":
        return OPENROUTER_API_KEY, bool(OPENROUTER_API_KEY) and not _is_placeholder(OPENROUTER_API_KEY)
    if provider == "huggingface":
        return HF_API_TOKEN, bool(HF_API_TOKEN) and not _is_placeholder(HF_API_TOKEN)
    if provider == "watsonx":
        ok = bool(WATSONX_API_KEY) and bool(WATSONX_PROJECT_ID)
        ok = ok and not _is_placeholder(WATSONX_API_KEY)
        return WATSONX_API_KEY, ok
    return "", False


# Initial load
reload_from_env()
