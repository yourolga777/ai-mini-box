import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_mini_box.cli import app as cli_app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def clean_business_config():
    yield
    path = Path("data/business_config.json")
    if path.exists():
        path.unlink()


def test_business_cli_listed(runner):
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0
    assert "business" in result.output


def test_business_show_smoke(runner):
    result = runner.invoke(cli_app, ["business", "show"])
    assert result.exit_code == 0
    assert "company_name" in result.output


def test_business_set_and_show(runner):
    result = runner.invoke(cli_app, ["business", "set", "company_name", "Магазин"])
    assert result.exit_code == 0
    assert "Updated" in result.output
    result = runner.invoke(cli_app, ["business", "show"])
    assert "Магазин" in result.output


def test_business_set_unknown_key(runner):
    result = runner.invoke(cli_app, ["business", "set", "nonexistent", "value"])
    assert result.exit_code == 1
    assert "Unknown" in result.output


def test_business_faq_add(runner):
    result = runner.invoke(cli_app, ["business", "faq", "add", "Вопрос?", "Ответ!"])
    assert result.exit_code == 0
    assert "Added FAQ" in result.output


def test_business_faq_remove(runner):
    result = runner.invoke(cli_app, ["business", "faq", "add", "Q1", "A1"])
    assert result.exit_code == 0
    result = runner.invoke(cli_app, ["business", "faq", "remove", "0"])
    assert result.exit_code == 0
    assert "Removed FAQ" in result.output


def test_business_faq_remove_out_of_range(runner):
    result = runner.invoke(cli_app, ["business", "faq", "remove", "99"])
    assert result.exit_code == 1
    assert "out of range" in result.output


def test_business_faq_remove_non_numeric(runner):
    result = runner.invoke(cli_app, ["business", "faq", "remove", "abc"])
    assert result.exit_code == 1
    assert "numeric" in result.output
