from unittest.mock import patch

import typer
from typer.testing import CliRunner

from ai_mini_box.core.services.registry import get_service, register_service


def test_register_creates_service():
    """Verify that after register(), get_service('llm') returns a service."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)  # clean slate
    app = typer.Typer()
    with patch("ai_mini_box_llm.plugin.LlmConfig.load") as mock_load:
        mock_config = mock_load.return_value
        mock_config.provider = "local"
        mock_config.model_path = "/dev/null/test.gguf"
        mock_config.n_ctx = 512
        mock_config.n_threads = 1
        mock_config.rag_enabled = False
        mock_config.rag_top_k = 3
        mock_config.rag_index_path = "data/llm_rag_index.json"

        with patch("ai_mini_box_llm.service._create_provider"):
            register(app)

    svc = get_service("llm")
    assert svc is not None
    assert hasattr(svc, "classify")
    assert hasattr(svc, "draft_response")
    assert hasattr(svc, "extract_entities")


def test_register_adds_typer_commands():
    """Verify that register() adds the 'llm' subcommand group."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)  # clean slate
    app = typer.Typer()
    with patch("ai_mini_box_llm.plugin.LlmConfig.load"):
        with patch("ai_mini_box_llm.plugin.LlmServiceImpl"):
            register(app)

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert "llm" in result.output


def test_register_handles_config_error_gracefully():
    """If config loading fails, plugin should not crash, just skip."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)  # clean slate

    app = typer.Typer()
    with patch("ai_mini_box_llm.plugin.LlmConfig.load", side_effect=Exception("config error")):
        register(app)

    svc = get_service("llm")
    assert svc is None  # service was NOT registered


def test_register_recovers_previous_registration():
    """Test registering then getting service between calls works."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)  # clean slate
    assert get_service("llm") is None

    app = typer.Typer()
    with patch("ai_mini_box_llm.plugin.LlmConfig.load") as mock_load:
        mock_cfg = mock_load.return_value
        mock_cfg.provider = "local"
        mock_cfg.model_path = "/dev/null/test.gguf"
        mock_cfg.n_ctx = 512
        mock_cfg.n_threads = 1
        mock_cfg.rag_enabled = False
        mock_cfg.rag_top_k = 3
        mock_cfg.rag_index_path = "data/llm_rag_index.json"
        with patch("ai_mini_box_llm.service._create_provider"):
            register(app)

    svc = get_service("llm")
    assert svc is not None

    svc2 = get_service("llm")
    assert svc2 is svc
