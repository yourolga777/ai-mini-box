from abc import ABC, abstractmethod
from typing import Any, Optional

from ai_mini_box.core.models import Topic


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> str:
        """Generate text from a prompt."""

    @abstractmethod
    def classify(self, text: str) -> Optional[Topic]:
        """Classify message topic."""

    @abstractmethod
    def draft_response(self, text: str, topic: Optional[Topic] = None) -> Optional[str]:
        """Generate a draft response."""

    @abstractmethod
    def extract_entities(self, text: str) -> dict[str, Any]:
        """Extract structured entities from text."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Get embedding vector for text (used by RAG)."""
