"""
Generic AI provider interface.
Implementations: HuggingFace (hf_client), watsonx (watsonx_client), mock (mock_provider).
Swap providers via config.LLM_PROVIDER without changing the orchestration pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ai.contracts import LLMResult, PromptResult, make_llm_result


class AIProvider(ABC):
    """All LLM backends must implement this contract."""

    @abstractmethod
    def complete(self, prompt: PromptResult, **kwargs: Any) -> LLMResult:
        """Accept PromptResult, return LLMResult."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


def wrap_llm_output(
    prompt: PromptResult,
    *,
    provider: str,
    model: str,
    text: str,
    usage: dict[str, Any] | None = None,
) -> LLMResult:
    return make_llm_result(
        request_id=prompt["request_id"],
        provider=provider,
        model=model,
        text=text,
        usage=usage,
    )
