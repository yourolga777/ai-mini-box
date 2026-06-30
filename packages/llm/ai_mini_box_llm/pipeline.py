from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class ProcessingContext:
    text: str
    history: list[dict] = field(default_factory=list)
    user_name: str = ""
    category: str | None = None
    contact_id: int | None = None
    business_config: dict | None = None


@dataclass
class PipelineResult:
    category: str = "ВОПРОС"
    confidence: float = 0.0
    need_human: bool = True
    reply_text: str | None = None
    reply_source: str = "fallback"
    entities: dict[str, Any] = field(default_factory=dict)
    is_order: bool = False
    template_id: str | None = None
    processing_time_ms: int = 0


def _time_ms() -> int:
    return int(time.time() * 1000)


def _fill_template(template_text: str, entities: dict[str, Any]) -> str:
    result = template_text
    for key, value in entities.items():
        result = result.replace("{{" + key + "}}", str(value) if value is not None else "")
        result = result.replace("{{ " + key + " }}", str(value) if value is not None else "")
    result = result.replace("{{name}}", entities.get("name", ""))
    result = result.replace("{{date}}", entities.get("date", ""))
    result = result.replace("{{time}}", entities.get("time", ""))
    result = result.replace("{{phone}}", entities.get("phone", ""))
    result = result.replace("{{address}}", entities.get("address", ""))
    result = result.replace("{{email}}", entities.get("email", ""))
    result = result.replace("{{order}}", str(entities.get("order_id", "")))
    return result


class Pipeline:
    def __init__(
        self,
        classifier,
        entity_extractor,
        template_selector,
        rag,
        cache,
    ):
        self._classifier = classifier
        self._extractor = entity_extractor
        self._template_selector = template_selector
        self._rag = rag
        self._cache = cache

    def process(self, text: str, context: ProcessingContext | None = None) -> PipelineResult:
        t0 = _time_ms()

        if not text:
            return PipelineResult(processing_time_ms=_time_ms() - t0)

        cached = self._cache.get(text)
        if cached:
            cached["processing_time_ms"] = _time_ms() - t0
            return PipelineResult(**cached)

        text = self._extractor.normalize(text)

        category, confidence = self._classifier.predict(text)
        is_order, _ = self._classifier.predict_order(text)

        entities = self._extractor.extract(text)

        rag_results = self._rag.retrieve(text) if self._rag.available else []

        rag_result = rag_results[0] if rag_results else None

        template = self._template_selector.find_best(category, text, entities, confidence, rag_result)

        reply_text = _fill_template(template.text, entities) if template else None

        need_human = (
            confidence < 0.6
            or (template and template.scope == "system" and category == "complaint" and confidence < 0.8)
        )

        result = PipelineResult(
            category=category,
            confidence=confidence,
            need_human=need_human,
            reply_text=reply_text,
            reply_source=template.scope if template else "fallback",
            entities=entities,
            is_order=is_order,
            template_id=getattr(template, "id", None) if template else None,
            processing_time_ms=_time_ms() - t0,
        )

        try:
            self._cache.set(text, result.__dict__, result.template_id)
        except Exception as e:
            logger.warning("Cache set failed: {}", e)

        return result
