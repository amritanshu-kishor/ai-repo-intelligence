"""
Google Gemini API provider (free tier via AI Studio).
"""

from __future__ import annotations

from typing import Any

import requests

from ai.contracts import LLMResult, PromptResult
from ai.mock_provider import MockProvider
from ai.provider_base import AIProvider, wrap_llm_output
from config import GEMINI_API_KEY, GEMINI_MODEL, LLM_MAX_TOKENS, LLM_SYSTEM_PROMPT


class GeminiProvider(AIProvider):
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_MODEL,
    ) -> None:
        self.api_key = api_key
        self.model = model

    def complete(self, prompt: PromptResult, **kwargs: Any) -> LLMResult:
        if not self.api_key:
            return MockProvider().complete(prompt, **kwargs)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        user_text = prompt.get("text", "")
        parts = []
        if LLM_SYSTEM_PROMPT:
            parts.append({"text": LLM_SYSTEM_PROMPT})
        parts.append({"text": user_text})

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.2),
                "maxOutputTokens": kwargs.get("max_tokens", LLM_MAX_TOKENS),
            },
        }

        response = requests.post(url, json=payload, timeout=120)
        if not response.ok:
            raise RuntimeError(f"Gemini API error {response.status_code}: {response.text[:400]}")

        data = response.json()
        text = ""
        for candidate in data.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text += part.get("text", "")

        return wrap_llm_output(
            prompt,
            provider=self.provider_name,
            model=self.model,
            text=text.strip() or "[Gemini returned empty response]",
        )
