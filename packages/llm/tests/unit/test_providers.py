from unittest.mock import MagicMock, patch

import pytest

from ai_mini_box.core.models import Topic
from ai_mini_box_llm.config import LlmConfig
from ai_mini_box_llm.providers.local import LocalProvider
from ai_mini_box_llm.providers.remote import RemoteProvider


@pytest.fixture
def local_config(tmp_path):
    return LlmConfig(
        provider="local",
        model_path=str(tmp_path / "model.gguf"),
        n_ctx=512,
        n_threads=1,
    )


@pytest.fixture
def remote_config():
    return LlmConfig(
        provider="remote",
        api_key="sk-test",
        api_url="https://api.openai.com/v1",
        model_name="gpt-3.5-turbo",
    )


class TestLocalProvider:
    def _make_provider(self, config, mock_model=None):
        mock_llama_module = MagicMock()
        mock_llama_module.Llama.return_value = mock_model or MagicMock()
        with patch.dict("sys.modules", {"llama_cpp": mock_llama_module}):
            with patch("pathlib.Path.exists", return_value=True):
                return LocalProvider(config)

    def test_classify_returns_topic(self, local_config):
        mock_model = MagicMock()
        mock_model.return_value = {"choices": [{"text": "PRICES"}]}
        provider = self._make_provider(local_config, mock_model)
        result = provider.classify("сколько стоит?")
        assert result == Topic.PRICES

    def test_classify_returns_none_on_empty_text(self, local_config):
        provider = self._make_provider(local_config)
        assert provider.classify("") is None
        assert provider.classify("   ") is None

    def test_extract_entities_returns_dict(self, local_config):
        mock_model = MagicMock()
        mock_model.return_value = {
            "choices": [{"text": '{"phone": "+71234567890", "name": "Alice"}'}]
        }
        provider = self._make_provider(local_config, mock_model)
        result = provider.extract_entities("Call Alice at +71234567890")
        assert result["phone"] == "+71234567890"
        assert result["name"] == "Alice"

    def test_draft_response_returns_string(self, local_config):
        mock_model = MagicMock()
        mock_model.return_value = {
            "choices": [{"text": "Sure, here you go."}]
        }
        provider = self._make_provider(local_config, mock_model)
        result = provider.draft_response("Hello", topic=Topic.ORDER)
        assert result == "Sure, here you go."

    def test_draft_response_none_on_empty(self, local_config):
        provider = self._make_provider(local_config)
        assert provider.draft_response("") is None

    def test_import_error_when_llama_missing(self, local_config):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.__import__", side_effect=ImportError("no llama")):
                with pytest.raises(ImportError, match="llama-cpp-python"):
                    LocalProvider(local_config)


class TestRemoteProvider:
    def _make_provider(self, config, register_openai=True):
        if register_openai:
            mock_openai_module = MagicMock()
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = ""
            mock_client.chat.completions.create.return_value.choices = [mock_choice]
            mock_openai_module.OpenAI.return_value = mock_client
            patcher = patch.dict("sys.modules", {"openai": mock_openai_module})
            patcher.start()
        else:
            patcher = None

        try:
            return RemoteProvider(config), mock_client if register_openai else None
        finally:
            if patcher:
                patcher.stop()

    def test_classify_returns_topic(self, remote_config):
        mock_openai_module = MagicMock()
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "PRICES"
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            provider = RemoteProvider(remote_config)
            result = provider.classify("сколько стоит?")
            assert result == Topic.PRICES

    def test_classify_returns_none_on_empty(self, remote_config):
        mock_openai_module = MagicMock()
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = ""
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            provider = RemoteProvider(remote_config)
            assert provider.classify("") is None

    def test_extract_entities(self, remote_config):
        mock_openai_module = MagicMock()
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"phone": "+71234567890"}'
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            provider = RemoteProvider(remote_config)
            result = provider.extract_entities("Call +71234567890")
            assert result["phone"] == "+71234567890"

    def test_draft_response(self, remote_config):
        mock_openai_module = MagicMock()
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Thank you for your order"
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            provider = RemoteProvider(remote_config)
            result = provider.draft_response("I want to order", topic=Topic.ORDER)
            assert result == "Thank you for your order"

    def test_embed(self, remote_config):
        mock_openai_module = MagicMock()
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.embedding = [0.1, 0.2, 0.3]
        mock_client.embeddings.create.return_value.data = [mock_choice]
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            provider = RemoteProvider(remote_config)
            result = provider.embed("test text")
            assert result == [0.1, 0.2, 0.3]

    def test_import_error_when_openai_missing(self, remote_config):
        with patch("builtins.__import__", side_effect=ImportError("no openai")):
            with pytest.raises(ImportError, match="openai"):
                RemoteProvider(remote_config)

    def test_value_error_when_no_api_key(self):
        cfg = LlmConfig(provider="remote", api_key="")
        mock_openai_module = MagicMock()
        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            with pytest.raises(ValueError, match="API key"):
                RemoteProvider(cfg)
