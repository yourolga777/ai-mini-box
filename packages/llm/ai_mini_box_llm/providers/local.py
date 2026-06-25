from __future__ import annotations

import json
import re
from typing import Any, Optional

from loguru import logger

from ai_mini_box.core.models import Topic

from ..config import LlmConfig
from ..prompt import CLASSIFY_PROMPT, DRAFT_PROMPT, DRAFT_PROMPT_NO_TOPIC, EXTRACT_PROMPT
from .base import BaseLLMProvider


_JSON_RE = re.compile(r"\{[^}]+\}")


class LocalProvider(BaseLLMProvider):
    def __init__(self, config: LlmConfig):
        self.config = config
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            import llama_cpp
        except ImportError:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Run: pip install ai-mini-box-llm[local]"
            )

        from pathlib import Path

        model_path = Path(self.config.model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {model_path.resolve()}. "
                f"Run 'ai-mini-box llm download-model' or set a valid model_path in config."
            )

        logger.info("Loading GGUF model from {}", model_path)
        self._model = llama_cpp.Llama(
            model_path=str(model_path),
            n_ctx=self.config.n_ctx,
            n_threads=self.config.n_threads,
            verbose=False,
        )
        logger.info("Model loaded: {} (ctx={}, threads={})", model_path.name, self.config.n_ctx, self.config.n_threads)

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> str:
        if self._model is None:
            return ""
        output = self._model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["\n"],
            echo=False,
        )
        return output["choices"][0]["text"].strip()

    def classify(self, text: str) -> Optional[Topic]:
        if not text.strip():
            return None
        try:
            raw = self.generate(CLASSIFY_PROMPT.format(text=text), max_tokens=10)
            label = raw.strip().upper()
            if label in Topic._member_map_:
                return Topic._member_map_[label]
            return None
        except Exception as e:
            logger.warning("Classification failed: {}", e)
            return None

    def draft_response(self, text: str, topic: Optional[Topic] = None) -> Optional[str]:
        if not text.strip():
            return None
        try:
            if topic:
                prompt = DRAFT_PROMPT.format(text=text, topic=topic.value, RAG_CONTEXT="")
            else:
                prompt = DRAFT_PROMPT_NO_TOPIC.format(text=text, RAG_CONTEXT="")
            result = self.generate(prompt, max_tokens=512, temperature=0.3)
            return result if result else None
        except Exception as e:
            logger.warning("Draft generation failed: {}", e)
            return None

    def extract_entities(self, text: str) -> dict[str, Any]:
        if not text.strip():
            return {}
        try:
            raw = self.generate(EXTRACT_PROMPT.format(text=text), max_tokens=256)
            m = _JSON_RE.search(raw)
            if m:
                return json.loads(m.group(0))
            return {}
        except Exception as e:
            logger.warning("Entity extraction failed: {}", e)
            return {}

    def embed(self, text: str) -> list[float]:
        if self._model is None:
            return []
        try:
            return self._model.create_embedding(text)["data"][0]["embedding"]
        except Exception as e:
            logger.warning("Embedding failed: {}", e)
            return []
