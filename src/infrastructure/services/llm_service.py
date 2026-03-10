"""OpenAI-compatible LLM service for answer synthesis."""

from __future__ import annotations

import logging
from typing import Any

import requests


logger = logging.getLogger(__name__)


class OpenAICompatibleLLMService:
    """Generate answers through an OpenAI-compatible chat-completions API."""

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str = "gpt-4o-mini",
        timeout_seconds: int = 90,
    ) -> None:
        self.api_key = api_key or "chatmock-local"
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self.timeout_seconds = timeout_seconds
        logger.info(
            "OpenAI-compatible LLM service initialized",
            extra={"model": model, "base_url": self.base_url},
        )

    def generate_answer(self, question: str, context: str) -> str:
        """Generate an answer from the supplied context."""
        try:
            response = self._chat(
                system_prompt=(
                    "You are an expert in Israeli planning and zoning regulations. "
                    "Answer only from the supplied context. If the context is insufficient, "
                    "say so clearly and stay concise."
                ),
                user_prompt=(
                    "Context:\n"
                    f"{context}\n\n"
                    "Question:\n"
                    f"{question}\n\n"
                    "Return a clear answer with direct references to the relevant regulation titles."
                ),
                temperature=0.1,
                max_tokens=1000,
            )
        except Exception as exc:
            logger.error("Error generating answer: %s", exc)
            return f"Error processing query: {exc}"

        content = self._extract_content(response)
        if content:
            return content.strip()
        return "Unable to generate answer from available regulations."

    def _chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _extract_content(payload: dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            return "\n".join(
                str(part.get("text", "")) for part in content if isinstance(part, dict)
            )
        return str(content)


# Backwards-compatible alias for modules that still import the legacy name.
GeminiLLMService = OpenAICompatibleLLMService
