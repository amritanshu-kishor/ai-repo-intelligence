"""
Local mock provider for hackathon demos without API credentials.
"""

from __future__ import annotations

from typing import Any

from ai.contracts import LLMResult, PromptResult
from ai.provider_base import AIProvider, wrap_llm_output


class MockProvider(AIProvider):
    provider_name = "mock"

    def complete(self, prompt: PromptResult, **kwargs: Any) -> LLMResult:
        preview = prompt.get("text", "")[:200].replace("\n", " ")
        text = (
            "[Mock LLM] Configure HF_API_TOKEN or watsonx credentials for live inference. "
            f"Prompt preview: {preview}..."
        )
        return wrap_llm_output(
            prompt,
            provider=self.provider_name,
            model=kwargs.get("model", "local-mock"),
            text=text,
        )
