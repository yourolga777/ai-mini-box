from unittest.mock import patch

import typer
from typer.testing import CliRunner

from ai_mini_box.core.services.registry import get_service, register_service


def test_register_creates_service():
    """Verify that after register(), get_service('llm') returns a Pipeline."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)  # clean slate
    app = typer.Typer()

    with (
        patch("ai_mini_box_llm.plugin._seed_system_categories"),
        patch("ai_mini_box_llm.plugin._init_pipeline") as mock_init,
    ):
        mock_pipeline = mock_init.return_value
        register(app)

    svc = get_service("llm")
    assert svc is not None
    assert hasattr(svc, "process")
    assert svc is mock_pipeline


def test_register_adds_typer_commands():
    """Verify that register() adds the 'llm' subcommand group."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)  # clean slate
    app = typer.Typer()
    with (
        patch("ai_mini_box_llm.plugin._seed_system_categories"),
        patch("ai_mini_box_llm.plugin._init_pipeline") as mock_init,
    ):
        mock_init.return_value = object()
        register(app)

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert "llm" in result.output


def test_register_handles_config_error_gracefully():
    """If pipeline init fails, plugin should not crash, just skip."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)  # clean slate

    app = typer.Typer()
    with (
        patch("ai_mini_box_llm.plugin._seed_system_categories"),
        patch("ai_mini_box_llm.plugin._init_pipeline", side_effect=Exception("init error")),
    ):
        register(app)

    svc = get_service("llm")
    assert svc is None  # pipeline was NOT registered


def test_assign_all_no_llm_shows_message():
    """assign-all without LLM prints 'LLM pipeline not configured'."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)
    register_service("auto_processor", None)
    app = typer.Typer()
    with (
        patch("ai_mini_box_llm.plugin._seed_system_categories"),
        patch("ai_mini_box_llm.plugin._init_pipeline", side_effect=Exception("no pipeline")),
    ):
        register(app)
        runner = CliRunner()
        result = runner.invoke(app, ["llm", "assign-all"])
    assert "LLM pipeline not configured" in result.output
    assert result.exit_code == 0


def test_process_daemon_help_shown():
    """process-daemon appears in llm help."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)
    app = typer.Typer()
    with (
        patch("ai_mini_box_llm.plugin._seed_system_categories"),
        patch("ai_mini_box_llm.plugin._init_pipeline") as mock_init,
    ):
        mock_init.return_value = object()
        register(app)

    runner = CliRunner()
    result = runner.invoke(app, ["llm", "--help"])
    assert "process-daemon" in result.output


def test_assign_all_help_shown():
    """assign-all appears in llm help."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)
    app = typer.Typer()
    with (
        patch("ai_mini_box_llm.plugin._seed_system_categories"),
        patch("ai_mini_box_llm.plugin._init_pipeline") as mock_init,
    ):
        mock_init.return_value = object()
        register(app)

    runner = CliRunner()
    result = runner.invoke(app, ["llm", "--help"])
    assert "assign-all" in result.output


def test_register_recovers_previous_registration():
    """Test registering then getting service between calls works."""
    from ai_mini_box_llm.plugin import register

    register_service("llm", None)  # clean slate
    assert get_service("llm") is None

    app = typer.Typer()
    with (
        patch("ai_mini_box_llm.plugin._seed_system_categories"),
        patch("ai_mini_box_llm.plugin._init_pipeline") as mock_init,
    ):
        mock_pipeline = mock_init.return_value
        register(app)

    svc = get_service("llm")
    assert svc is not None
    assert svc is mock_pipeline

    svc2 = get_service("llm")
    assert svc2 is svc
