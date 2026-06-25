from unittest.mock import MagicMock, patch

import pytest

from ai_mini_box.core.models import Topic
from ai_mini_box.core.services.registry import get_service, register_service
from ai_mini_box_llm.config import LlmConfig
from ai_mini_box_llm.service import LlmServiceImpl


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.classify.return_value = Topic.PRICES
    provider.generate.return_value = "Test draft"
    provider.extract_entities.return_value = {"phone": "+71234567890"}
    return provider


@pytest.fixture
def service(mock_provider):
    config = LlmConfig(provider="local", model_path="test.gguf")
    with patch("ai_mini_box_llm.service._create_provider", return_value=mock_provider):
        svc = LlmServiceImpl(config)
        return svc


class TestLlmServiceImpl:
    def test_classify(self, service, mock_provider):
        result = service.classify("сколько стоит?")
        assert result == Topic.PRICES
        mock_provider.classify.assert_called_once_with("сколько стоит?")

    def test_classify_returns_none(self, service, mock_provider):
        mock_provider.classify.return_value = None
        result = service.classify("blah")
        assert result is None

    def test_draft_response(self, service, mock_provider):
        result = service.draft_response("I want to order", topic=Topic.ORDER)
        assert result == "Test draft"
        assert mock_provider.generate.called

    def test_draft_response_no_topic(self, service, mock_provider):
        mock_provider.generate.return_value = "Generated draft"
        result = service.draft_response("Hello")
        assert result == "Generated draft"

    def test_extract_entities(self, service, mock_provider):
        result = service.extract_entities("Call +71234567890")
        assert result["phone"] == "+71234567890"

    def test_unknown_provider_raises(self):
        config = LlmConfig(provider="nonexistent")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LlmServiceImpl(config)

    def test_registration_with_registry(self, service):
        register_service("llm", service)
        retrieved = get_service("llm")
        assert retrieved is service
        assert retrieved.classify("test") == Topic.PRICES

    def test_rag_context_in_draft(self, mock_provider):
        config = LlmConfig(provider="local", model_path="test.gguf", rag_enabled=True)
        mock_provider.generate.return_value = "RAG draft"
        with patch("ai_mini_box_llm.service._create_provider", return_value=mock_provider):
            with patch("ai_mini_box_llm.service.retrieve_context", return_value="KB context"):
                svc = LlmServiceImpl(config)
                result = svc.draft_response("Hello", topic=Topic.ORDER)
                assert result == "RAG draft"
