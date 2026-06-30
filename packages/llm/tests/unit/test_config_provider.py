import importlib.metadata
from unittest.mock import MagicMock, patch

from ai_mini_box_llm.plugin import LlmConfigProvider, config_provider


def test_get_config_returns_all_fields():
    """get_config() returns all expected fields."""
    with patch("ai_mini_box_llm.plugin.LlmConfig.load") as mock_load:
        mock_cfg = MagicMock()
        mock_cfg.provider = "local"
        mock_cfg.model_path = ""
        mock_cfg.rag_enabled = False
        mock_cfg.rag_top_k = 3
        mock_load.return_value = mock_cfg
        result = config_provider.get_config()
    assert "provider" in result
    assert "model_path" in result
    assert "embeddings_model" in result
    assert "rag_enabled" in result
    assert "rag_top_k" in result
    assert "confidence_min" in result
    assert "batch_size" in result


def test_set_config_updates_only_given_field():
    """set_config({"rag_top_k": 5}) updates only rag_top_k."""
    with patch("ai_mini_box_llm.plugin.LlmConfig.load") as mock_load:
        mock_cfg = MagicMock()
        mock_cfg.provider = "local"
        mock_cfg.model_path = ""
        mock_cfg.rag_enabled = False
        mock_cfg.rag_top_k = 3
        mock_load.return_value = mock_cfg

        provider = LlmConfigProvider()
        provider.set_config({"rag_top_k": 5})

    assert mock_cfg.rag_top_k == 5
    assert mock_cfg.provider == "local"


def test_set_config_handles_rag_enabled_boolean():
    """set_config({"rag_enabled": True}) saves bool correctly."""
    with patch("ai_mini_box_llm.plugin.LlmConfig.load") as mock_load:
        mock_cfg = MagicMock()
        mock_cfg.provider = "local"
        mock_cfg.model_path = ""
        mock_cfg.rag_enabled = False
        mock_cfg.rag_top_k = 3
        mock_load.return_value = mock_cfg

        provider = LlmConfigProvider()
        provider.set_config({"rag_enabled": True})

    assert mock_cfg.rag_enabled is True


def test_get_schema_returns_valid_json_schema():
    """get_schema() returns a valid JSON Schema."""
    schema = config_provider.get_schema()
    assert schema["$schema"] == "https://json-schemas.org/draft/2020-12/schema"
    assert "properties" in schema
    assert "provider" in schema["properties"]
    assert "rag_top_k" in schema["properties"]
    assert "confidence_min" in schema["properties"]
    assert "batch_size" in schema["properties"]
    assert "rag_enabled" in schema["properties"]
    assert "embeddings_model" in schema["properties"]


def test_entry_point_registered():
    """Entry point ai_mini_box.config_provider is registered."""
    eps = importlib.metadata.entry_points(group="ai_mini_box.config_provider")
    assert len(eps) > 0
    llm_ep = [ep for ep in eps if ep.name == "llm"]
    assert len(llm_ep) == 1
    provider = llm_ep[0].load()
    assert provider is config_provider
