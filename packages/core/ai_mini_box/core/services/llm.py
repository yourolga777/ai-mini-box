from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ai_mini_box.core.models import Topic


class LlmService(ABC):
    """Abstract LLM service — implemented by ai-mini-box-llm plugin."""

    @abstractmethod
    def classify(self, text: str) -> Topic | None:
        ...

    @abstractmethod
    def draft_response(self, text: str, topic: Topic | None = None) -> str | None:
        ...

    @abstractmethod
    def extract_entities(self, text: str) -> dict[str, Any]:
        ...


class NullLlmService(LlmService):
    """Fallback when no LLM plugin is installed — all methods return None/empty."""

    def classify(self, text: str) -> None:
        return None

    def draft_response(self, text: str, topic: Topic | None = None) -> None:
        return None

    def extract_entities(self, text: str) -> dict[str, Any]:
        return {}
