"""OpenAI-compatible LLM service for answer synthesis."""

from __future__ import annotations

import logging
from typing import Any

import requests


logger = logging.getLogger(__name__)


def probe_openai_compatible_provider(
    *,
    base_url: str,
    api_key: str | None,
    timeout_seconds: int = 5,
) -> dict[str, Any]:
    """Probe an OpenAI-compatible provider without generating content."""
    endpoint = f"{base_url.rstrip('/')}/models"
    headers = {
        "Authorization": f"Bearer {api_key or 'chatmock-local'}",
        "Accept": "application/json",
    }
    try:
        response = requests.get(endpoint, headers=headers, timeout=timeout_seconds)
    except Exception as exc:
        return {
            "healthy": False,
            "status": "unreachable",
            "endpoint": endpoint,
            "detail": str(exc),
        }

    content_type = response.headers.get("content-type", "")
    if not response.ok:
        return {
            "healthy": False,
            "status": "http_error",
            "endpoint": endpoint,
            "status_code": response.status_code,
            "content_type": content_type,
            "detail": response.text[:240],
        }

    if "json" not in content_type.lower():
        return {
            "healthy": False,
            "status": "invalid_content_type",
            "endpoint": endpoint,
            "status_code": response.status_code,
            "content_type": content_type,
            "detail": "Provider returned non-JSON content. Check that OPENAI_BASE_URL points to the API endpoint, not a web UI.",
        }

    try:
        payload = response.json()
    except ValueError as exc:
        return {
            "healthy": False,
            "status": "invalid_json",
            "endpoint": endpoint,
            "status_code": response.status_code,
            "content_type": content_type,
            "detail": str(exc),
        }

    models = payload.get("data") if isinstance(payload, dict) else None
    return {
        "healthy": True,
        "status": "ready",
        "endpoint": endpoint,
        "status_code": response.status_code,
        "content_type": content_type,
        "model_count": len(models) if isinstance(models, list) else None,
    }


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

    def probe(self) -> dict[str, Any]:
        """Report whether the configured provider appears OpenAI-compatible."""
        return probe_openai_compatible_provider(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout_seconds=min(self.timeout_seconds, 5),
        )


# Backwards-compatible alias for modules that still import the legacy name.
GeminiLLMService = OpenAICompatibleLLMService
