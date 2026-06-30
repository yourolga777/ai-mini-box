from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai_mini_box.core.models import Contact, Message
from ai_mini_box_llm.auto_processor import AutoProcessor, AutoProcessResult


@pytest.fixture
def mock_repos():
    repos = MagicMock()
    repos.contacts.update.return_value = None
    repos.tasks.add.return_value = None
    return repos


class _MockPipeline:
    def process(self, text, context=None):
        from ai_mini_box_llm.pipeline import PipelineResult
        return PipelineResult(
            category="ВОПРОС",
            confidence=0.9,
            need_human=False,
            reply_text="Ответ",
            reply_source="template",
            entities={},
            is_order=False,
            processing_time_ms=5,
        )


class TestAutoProcessor:
    def test_no_repos_creates_own_session(self):
        processor = AutoProcessor()
        assert processor._repos is None

    def test_no_pipeline_returns_early(self, mock_repos):
        processor = AutoProcessor(mock_repos)
        msg = Message(text="hello")
        contact = Contact(id=1, name="Client")
        with patch("ai_mini_box_llm.auto_processor.get_service", return_value=None):
            result = processor.process(msg, contact)
        assert isinstance(result, AutoProcessResult)
        assert result.contact_updated is False
        assert result.task_created is False
        assert result.folder_assigned is False

    def test_no_pipeline_process_all_returns_tuple(self, mock_repos):
        processor = AutoProcessor(mock_repos)
        with patch("ai_mini_box_llm.auto_processor.get_service", return_value=None):
            result = processor.process_all(limit=10)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_pipeline_updates_phone(self, mock_repos):
        processor = AutoProcessor(mock_repos)
        mock_pipeline = MagicMock()
        mock_pipeline.process.return_value = MagicMock(
            category="ВОПРОС", confidence=0.9, need_human=False,
            reply_text=None, reply_source="fallback",
            entities={"phone": "+79991234567"},
            is_order=False, template_id=None, processing_time_ms=5,
        )
        msg = Message(text="мой телефон +79991234567")
        contact = Contact(id=1, name="Client")
        with patch("ai_mini_box_llm.auto_processor.get_service", return_value=mock_pipeline):
            result = processor.process(msg, contact)
        assert contact.phone == "+79991234567"

    def test_pipeline_creates_order(self, mock_repos):
        processor = AutoProcessor(mock_repos)
        mock_pipeline = MagicMock()
        mock_pipeline.process.return_value = MagicMock(
            category="ЗАКАЗ", confidence=0.95, need_human=False,
            reply_text=None, reply_source="template",
            entities={},
            is_order=True, template_id=None, processing_time_ms=5,
        )
        mock_order = MagicMock()
        mock_order.id = 42
        mock_repos.orders.add.return_value = mock_order
        msg = Message(text="хочу заказать пиццу")
        contact = Contact(id=1, name="Client")
        with patch("ai_mini_box_llm.auto_processor.get_service", return_value=mock_pipeline):
            result = processor.process(msg, contact)
        assert result.order_created is True
        mock_repos.orders.add.assert_called_once()

    def test_process_all_empty_when_skip_existing(self, mock_repos):
        processor = AutoProcessor(mock_repos)
        mock_repos.messages.list.return_value = []
        with patch("ai_mini_box_llm.auto_processor.get_service", return_value=None):
            total, assigned = processor.process_all(limit=10)
        assert total == 0
        assert assigned == 0

    def test_auto_process_result_dataclass(self):
        r = AutoProcessResult()
        assert r.contact_updated is False
        assert r.task_created is False
        r2 = AutoProcessResult(contact_updated=True, order_created=True)
        assert r2.contact_updated is True
        assert r2.order_created is True
