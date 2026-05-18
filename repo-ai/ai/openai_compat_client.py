"""
OpenAI-compatible chat API client (Groq, OpenRouter, local LM Studio, etc.).
"""

from __future__ import annotations

from typing import Any

import requests
from requests.exceptions import JSONDecodeError

from ai.contracts import LLMResult, PromptResult
from ai.mock_provider import MockProvider
from ai.provider_base import AIProvider, wrap_llm_output


class OpenAICompatibleProvider(AIProvider):
    """Shared implementation for OpenAI-style /v1/chat/completions endpoints."""

    def __init__(
        self,
        *,
        provider_name: str,
        api_key: str,
        base_url: str,
        model: str,
        system_prompt: str = "",
    ) -> None:
        self._provider_name = provider_name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.system_prompt = system_prompt

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def complete(self, prompt: PromptResult, **kwargs: Any) -> LLMResult:
        if not self.api_key:
            return MockProvider().complete(prompt, **kwargs)

        url = self.base_url
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        messages: list[dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt.get("text", "")})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.2),
        }

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=kwargs.get("timeout", 120),
        )

        data = _parse_response(response, provider=self.provider_name)
        text = _extract_text(data)

        return wrap_llm_output(
            prompt,
            provider=self.provider_name,
            model=self.model,
            text=text,
        )


def _parse_response(response: requests.Response, *, provider: str = "llm") -> dict[str, Any]:
    if not response.ok:
        if response.status_code in (401, 403):
            raise RuntimeError(
                f"Invalid API key for {provider} (HTTP {response.status_code}). "
                f"Update repo-ai/.env, then restart the Flask server (Ctrl+C → python app.py). "
                f"Get a free key: Groq https://console.groq.com | Gemini https://aistudio.google.com/apikey"
            )
        preview = (response.text or "")[:400]
        raise RuntimeError(f"API error {response.status_code}: {preview}")
    try:
        return response.json()
    except JSONDecodeError as exc:
        preview = (response.text or "")[:400]
        raise RuntimeError(f"Non-JSON response ({response.status_code}): {preview}") from exc


def _extract_text(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if content:
            return str(content).strip()
    return str(data.get("error", data)).strip()
