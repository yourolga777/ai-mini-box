from __future__ import annotations

from unittest.mock import MagicMock

from ai_mini_box_llm.cache import ResponseCache
from ai_mini_box_llm.classifier import ClassifierEnsemble
from ai_mini_box_llm.extractor import EntityExtractor
from ai_mini_box_llm.pipeline import Pipeline, PipelineResult, ProcessingContext


class _MockClassifier:
    def predict(self, text):
        return ("ВОПРОС", 0.85)

    def predict_order(self, text):
        return (False, 0.95)

    def predict_folder(self, text, folder_names):
        return None

    def _fitted(self):
        return True


class _MockTemplateStore:
    def find_best(self, category, text, entities, confidence, rag_result=None):
        t = MagicMock()
        t.scope = "template"
        t.text = "Ответ на {{category}}"
        t.id = "tpl-1"
        return t


class _MockRag:
    available = True

    def retrieve(self, text, top_k=3):
        return [("релевантный ответ", 0.85, {"answer": "да, конечно"})]


class TestPipeline:
    def setup_method(self):
        self.pipeline = Pipeline(
            classifier=_MockClassifier(),
            entity_extractor=EntityExtractor(),
            template_selector=_MockTemplateStore(),
            rag=_MockRag(),
            cache=ResponseCache(maxsize=100, ttl_seconds=3600),
        )

    def test_process_returns_result(self):
        result = self.pipeline.process("Сколько стоит доставка?")
        assert isinstance(result, PipelineResult)
        assert result.category == "ВОПРОС"
        assert result.confidence > 0
        assert result.processing_time_ms >= 0

    def test_confidence_below_06_needs_human(self):
        pipeline = Pipeline(
            classifier=MagicMock(
                predict=lambda t: ("ВОПРОС", 0.3),
                predict_order=lambda t: (False, 0.5),
                _fitted=True,
            ),
            entity_extractor=EntityExtractor(),
            template_selector=_MockTemplateStore(),
            rag=_MockRag(),
            cache=ResponseCache(maxsize=100, ttl_seconds=3600),
        )
        result = pipeline.process("тест")
        assert result.need_human is True

    def test_confidence_high_no_human(self):
        result = self.pipeline.process("сколько стоит?")
        assert result.confidence >= 0.6
        assert result.need_human is False

    def test_empty_text_returns_early(self):
        result = self.pipeline.process("")
        assert result.category == "ВОПРОС"
        assert result.processing_time_ms >= 0

    def test_caching_works(self):
        result1 = self.pipeline.process("повтор")
        result2 = self.pipeline.process("повтор")
        assert result2.reply_source == "template"
        assert isinstance(result2, PipelineResult)

    def test_cache_hit_is_fast(self):
        self.pipeline.process("быстро")
        result = self.pipeline.process("быстро")
        assert result.processing_time_ms < 1000

    def test_entities_in_result(self):
        result = self.pipeline.process("меня зовут Иван, +7 999 123-45-67")
        assert "name" in result.entities or "phone" in result.entities

    def test_is_order_in_result(self):
        result = self.pipeline.process("спасибо")
        assert isinstance(result.is_order, bool)
