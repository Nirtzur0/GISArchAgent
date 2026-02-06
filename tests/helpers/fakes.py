"""Test fakes for external boundaries (LLM, vision, etc.)."""

from __future__ import annotations


class FakeLLM:
    def __init__(self, answer: str = "fake-answer"):
        self._answer = answer
        self.calls: list[dict] = []

    def generate_answer(self, *, question: str, context: str) -> str:
        self.calls.append({"question": question, "context": context})
        return self._answer

