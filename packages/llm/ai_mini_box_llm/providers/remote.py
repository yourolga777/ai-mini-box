from __future__ import annotations

import json
import re
from typing import Any, Optional

from loguru import logger

from ai_mini_box.core.models import Topic

from ..config import LlmConfig
from ..prompt import CLASSIFY_PROMPT, DRAFT_PROMPT, DRAFT_PROMPT_NO_TOPIC, EXTRACT_PROMPT, RAG_CONTEXT_TEMPLATE
from .base import BaseLLMProvider


_JSON_RE = re.compile(r"\{[^}]+\}")
_MODEL_DEFAULT = "gpt-3.5-turbo"


class RemoteProvider(BaseLLMProvider):
    def __init__(self, config: LlmConfig):
        self.config = config
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai is not installed. "
                "Run: pip install ai-mini-box-llm[remote]"
            )

        if not self.config.api_key:
            raise ValueError(
                "OpenAI API key is not set. Set api_key in data/llm_config.json "
                "or AI_BOX_LLM_API_KEY environment variable."
            )

        kwargs = {"api_key": self.config.api_key}
        if self.config.api_url:
            kwargs["base_url"] = self.config.api_url
        self._client = OpenAI(**kwargs)

    @property
    def _model_name(self) -> str:
        return self.config.model_name or _MODEL_DEFAULT

    def _chat(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> str:
        if self._client is None:
            return ""
        resp = self._client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> str:
        return self._chat(prompt, max_tokens=max_tokens, temperature=temperature)

    def classify(self, text: str) -> Optional[Topic]:
        if not text.strip():
            return None
        try:
            raw = self._chat(CLASSIFY_PROMPT.format(text=text), max_tokens=10)
            label = raw.strip().upper()
            if label in Topic._member_map_:
                return Topic._member_map_[label]
            return None
        except Exception as e:
            logger.warning("Remote classification failed: {}", e)
            return None

    def draft_response(self, text: str, topic: Optional[Topic] = None) -> Optional[str]:
        if not text.strip():
            return None
        try:
            if topic:
                prompt = DRAFT_PROMPT.format(text=text, topic=topic.value, RAG_CONTEXT="")
            else:
                prompt = DRAFT_PROMPT_NO_TOPIC.format(text=text, RAG_CONTEXT="")
            result = self._chat(prompt, max_tokens=512, temperature=0.3)
            return result if result else None
        except Exception as e:
            logger.warning("Remote draft generation failed: {}", e)
            return None

    def extract_entities(self, text: str) -> dict[str, Any]:
        if not text.strip():
            return {}
        try:
            raw = self._chat(EXTRACT_PROMPT.format(text=text), max_tokens=256)
            m = _JSON_RE.search(raw)
            if m:
                return json.loads(m.group(0))
            return {}
        except Exception as e:
            logger.warning("Remote entity extraction failed: {}", e)
            return {}

    def embed(self, text: str) -> list[float]:
        if self._client is None:
            return []
        try:
            resp = self._client.embeddings.create(
                model="text-embedding-ada-002",
                input=text,
            )
            return resp.data[0].embedding
        except Exception as e:
            logger.warning("Remote embedding failed: {}", e)
            return []
