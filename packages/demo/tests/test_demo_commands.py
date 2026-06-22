from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from ai_mini_box.core.models import Contact
from ai_mini_box.testing import MockContactRepo


@pytest.fixture
def app():
    import typer
    from ai_mini_box_demo.commands import register

    tapp = typer.Typer()
    register(tapp)
    return tapp


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_repo():
    repo = MockContactRepo()
    repo.add(Contact(id=1, name="Alice", phone="+111"))
    repo.add(Contact(id=2, name="Bob", phone="+222"))
    return repo


def test_demo_list_shows_contacts(app, runner, mock_repo):
    with patch("ai_mini_box_demo.commands.RepoContainer") as MockContainer:
        MockContainer.return_value.contacts = mock_repo
        with patch("ai_mini_box_demo.commands.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = MagicMock()

            result = runner.invoke(app, ["demo-list"])

    assert result.exit_code == 0
    assert "Alice" in result.output
    assert "Bob" in result.output
    assert "+111" in result.output


def test_demo_list_limit(app, runner, mock_repo):
    with patch("ai_mini_box_demo.commands.RepoContainer") as MockContainer:
        MockContainer.return_value.contacts = mock_repo
        with patch("ai_mini_box_demo.commands.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = MagicMock()

            result = runner.invoke(app, ["demo-list", "--limit", "1"])

    assert result.exit_code == 0


def test_demo_get_existing(app, runner, mock_repo):
    with patch("ai_mini_box_demo.commands.RepoContainer") as MockContainer:
        MockContainer.return_value.contacts = mock_repo
        with patch("ai_mini_box_demo.commands.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = MagicMock()

            result = runner.invoke(app, ["demo-get", "1"])

    assert result.exit_code == 0
    assert "Alice" in result.output
    assert "+111" in result.output


def test_demo_get_not_found(app, runner, mock_repo):
    with patch("ai_mini_box_demo.commands.RepoContainer") as MockContainer:
        MockContainer.return_value.contacts = mock_repo
        with patch("ai_mini_box_demo.commands.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = MagicMock()

            result = runner.invoke(app, ["demo-get", "999"])

    assert result.exit_code == 1
    assert "not found" in result.output


def test_demo_add(app, runner, mock_repo):
    with patch("ai_mini_box_demo.commands.RepoContainer") as MockContainer:
        MockContainer.return_value.contacts = mock_repo
        with patch("ai_mini_box_demo.commands.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = MagicMock()

            result = runner.invoke(app, ["demo-add", "Charlie", "--phone", "+333"])

    assert result.exit_code == 0
    assert "Charlie" in result.output
