"""
Hugging Face Inference API — isolated implementation.
Uses the router chat-completions API (OpenAI-compatible).
Do not import from orchestration code; use ai_provider.get_provider() instead.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.exceptions import JSONDecodeError

from ai.contracts import LLMResult, PromptResult
from ai.mock_provider import MockProvider
from ai.provider_base import AIProvider, wrap_llm_output
from config import HF_API_TOKEN, HF_INFERENCE_URL, HF_MODEL


class HuggingFaceProvider(AIProvider):
    """API replacement point: Hugging Face Inference Providers (router)."""

    provider_name = "huggingface"

    def __init__(
        self,
        token: str = HF_API_TOKEN,
        url: str = HF_INFERENCE_URL,
        model: str = HF_MODEL,
    ) -> None:
        self.token = token
        self.url = url
        self.model = model

    def complete(self, prompt: PromptResult, **kwargs: Any) -> LLMResult:
        if not self.token:
            return MockProvider().complete(prompt, **kwargs)

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt.get("text", "")}],
            "max_tokens": kwargs.get("max_tokens", 512),
        }

        response = requests.post(
            self.url, headers=headers, json=payload, timeout=120
        )

        data = _parse_response(response)
        text = _extract_hf_text(data)

        return wrap_llm_output(
            prompt,
            provider=self.provider_name,
            model=self.model,
            text=text,
        )


def _parse_response(response: requests.Response) -> dict[str, Any] | list[Any]:
    """Handle non-JSON error bodies (e.g. HTML 404 from deprecated endpoints)."""
    if not response.ok:
        body_preview = (response.text or "")[:400]
        raise RuntimeError(
            f"Hugging Face API error {response.status_code}: {body_preview}"
        )
    try:
        return response.json()
    except JSONDecodeError as exc:
        body_preview = (response.text or "")[:400]
        raise RuntimeError(
            f"Hugging Face returned non-JSON (status {response.status_code}): "
            f"{body_preview}"
        ) from exc


def _extract_hf_text(data: object) -> str:
    # Chat completions (router /v1/chat/completions)
    if isinstance(data, dict) and "choices" in data:
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content", "")
            if content:
                return str(content).strip()

    # Legacy text-generation shape
    if isinstance(data, list) and data:
        return str(data[0].get("generated_text", "")).strip()
    if isinstance(data, dict):
        return str(
            data.get("generated_text", data.get("answer", ""))
        ).strip()
    return str(data).strip()
