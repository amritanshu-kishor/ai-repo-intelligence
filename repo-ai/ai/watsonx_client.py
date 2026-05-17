"""
WatsonX AI provider implementation.
Implements AIProvider contract for IBM watsonx.ai Runtime integration.
"""

from __future__ import annotations

from ibm_watsonx_ai.foundation_models import Model

from ai.contracts import LLMResult, PromptResult
from ai.provider_base import AIProvider, wrap_llm_output
from config import (
    WATSONX_API_KEY,
    WATSONX_MODEL_ID,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
)


class WatsonxProvider(AIProvider):
    """IBM watsonx.ai Runtime provider with proper contract compliance."""

    def __init__(self):
        """Initialize watsonx.ai model with credentials."""
        credentials = {
            "url": WATSONX_URL,
            "apikey": WATSONX_API_KEY
        }

        self.model = Model(
            model_id=WATSONX_MODEL_ID,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
        )

    @property
    def provider_name(self) -> str:
        """Return provider identifier for logging and provenance."""
        return "watsonx"

    def complete(self, prompt: PromptResult, **kwargs) -> LLMResult:
        """
        Accept PromptResult contract, return LLMResult contract.
        
        CRITICAL: Increased max_new_tokens to preserve graph reasoning quality.
        Previous 300 token limit was truncating dependency chains and impact analysis.
        """
        prompt_text = prompt.get("text", "")
        request_id = prompt.get("request_id", "unknown")

        if not prompt_text or not prompt_text.strip():
            return wrap_llm_output(
                prompt,
                provider=self.provider_name,
                model=WATSONX_MODEL_ID,
                text="[Error: Empty prompt provided to watsonx provider]",
                usage={"error": "empty_prompt"},
            )

        try:
            # Increased token limits to preserve graph reasoning outputs
            response = self.model.generate_text(
                prompt=prompt_text,
                params={
                    "decoding_method": "greedy",
                    "max_new_tokens": 1500,  # Increased from 300 to preserve reasoning
                    "min_new_tokens": 50,     # Increased from 30 for better quality
                    "temperature": 0.2,
                    "repetition_penalty": 1.1,
                }
            )

            # Ensure response is clean text (watsonx returns str directly)
            text = str(response).strip() if response else ""
            
            if not text:
                text = "[Error: watsonx returned empty response]"

            return wrap_llm_output(
                prompt,
                provider=self.provider_name,
                model=WATSONX_MODEL_ID,
                text=text,
                usage={
                    "request_id": request_id,
                    "model": WATSONX_MODEL_ID,
                },
            )

        except Exception as e:
            # Defensive error handling with fallback
            error_msg = f"[WatsonX Error: {str(e)}]"
            return wrap_llm_output(
                prompt,
                provider=self.provider_name,
                model=WATSONX_MODEL_ID,
                text=error_msg,
                usage={"error": str(e), "request_id": request_id},
            )