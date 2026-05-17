"""
Provider factory — single entry for the orchestration pipeline.
"""

from __future__ import annotations

from ai.contracts import LLMResult, PromptResult
from ai.hf_client import HuggingFaceProvider
from ai.mock_provider import MockProvider
from ai.provider_base import AIProvider
from ai.watsonx_client import WatsonxProvider
from config import LLM_PROVIDER, USE_MOCK_LLM


def get_provider() -> AIProvider:
    if USE_MOCK_LLM:
        return MockProvider()
    if LLM_PROVIDER == "watsonx":
        return WatsonxProvider()
    if LLM_PROVIDER == "huggingface":
        return HuggingFaceProvider()
    raise ValueError(
        f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. "
        "Please set LLM_PROVIDER to 'watsonx' or 'huggingface' in your .env file, "
        "and ensure the corresponding API credentials are configured."
    )


def complete(prompt: PromptResult) -> LLMResult:
    """Stage 5: AI Provider Call."""
    return get_provider().complete(prompt)
