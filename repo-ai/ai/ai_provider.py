"""
Provider factory — single entry for the orchestration pipeline.
"""

from __future__ import annotations

from ai.contracts import LLMResult, PromptResult
from ai.gemini_client import GeminiProvider
from ai.hf_client import HuggingFaceProvider
from ai.mock_provider import MockProvider
from ai.openai_compat_client import OpenAICompatibleProvider
from ai.provider_base import AIProvider
from ai.watsonx_client import WatsonxProvider


def get_provider() -> AIProvider:
    import config as cfg
    cfg.reload_from_env()

    if cfg.USE_MOCK_LLM:
        return MockProvider()

    provider = cfg.LLM_PROVIDER

    if provider == "mock":
        return MockProvider()
    if provider == "groq":
        return OpenAICompatibleProvider(
            provider_name="groq",
            api_key=cfg.GROQ_API_KEY,
            base_url=cfg.GROQ_API_URL,
            model=cfg.GROQ_MODEL,
            system_prompt=cfg.LLM_SYSTEM_PROMPT,
        )
    if provider == "openrouter":
        return OpenAICompatibleProvider(
            provider_name="openrouter",
            api_key=cfg.OPENROUTER_API_KEY,
            base_url=cfg.OPENROUTER_API_URL,
            model=cfg.OPENROUTER_MODEL,
            system_prompt=cfg.LLM_SYSTEM_PROMPT,
        )
    if provider == "gemini":
        return GeminiProvider()
    if provider == "watsonx":
        return WatsonxProvider()
    if provider == "huggingface":
        return HuggingFaceProvider()

    raise ValueError(
        f"Invalid LLM_PROVIDER: {cfg.LLM_PROVIDER!r}. "
        "Set LLM_PROVIDER to one of: groq, gemini, openrouter, huggingface, watsonx, mock. "
        "Copy repo-ai/.env.example to repo-ai/.env and add your API key."
    )


def complete(prompt: PromptResult) -> LLMResult:
    """Stage 5: AI Provider Call."""
    return get_provider().complete(prompt)
