from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from ai_mini_box.core.models import Topic
from ai_mini_box.core.services.llm import LlmService

from .config import LlmConfig
from .providers.base import BaseLLMProvider
from .providers.local import LocalProvider
from .providers.remote import RemoteProvider
from .rag.retriever import retrieve_context


def _create_provider(config: LlmConfig) -> BaseLLMProvider:
    if config.provider == "local":
        return LocalProvider(config)
    elif config.provider == "remote":
        return RemoteProvider(config)
    else:
        raise ValueError(f"Unknown LLM provider: {config.provider!r}. Supported: local, remote.")


class LlmServiceImpl(LlmService):
    def __init__(self, config: LlmConfig):
        self.config = config
        self.provider = _create_provider(config)
        logger.info(
            "LLM service initialized: provider={}, model={}",
            config.provider,
            config.model_path if config.provider == "local" else config.model_name or "default",
        )

    def classify(self, text: str) -> Optional[Topic]:
        return self.provider.classify(text)

    def draft_response(self, text: str, topic: Optional[Topic] = None) -> Optional[str]:
        rag_context = ""
        if self.config.rag_enabled:
            rag_context = retrieve_context(
                self.provider,
                text,
                top_k=self.config.rag_top_k,
                index_path=self.config.rag_index_path,
            )

        if topic:
            prompt = (
                f"Topic: {topic.value}\n"
                f"Customer message: {text}\n\n"
                f"{rag_context}\n\n"
                f"Your response:"
            )
        else:
            prompt = (
                f"Customer message: {text}\n\n"
                f"{rag_context}\n\n"
                f"Your response:"
            )
        return self.provider.generate(prompt, max_tokens=512, temperature=0.3) or None

    def extract_entities(self, text: str) -> dict[str, Any]:
        return self.provider.extract_entities(text)
