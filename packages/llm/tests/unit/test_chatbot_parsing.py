from __future__ import annotations

from ai_mini_box_llm.pipeline import _fill_template
from ai_mini_box_llm.utils import parse_json


def test_parse_clean_json():
    raw = '{"category": "ЗАКАЗ", "reply_to_user": "Хорошо"}'
    result = parse_json(raw)
    assert result is not None
    assert result["category"] == "ЗАКАЗ"


def test_parse_json_with_prefix():
    raw = 'Вот JSON: {"category": "ВОПРОС", "reply_to_user": "Да"}'
    result = parse_json(raw)
    assert result is not None
    assert result["category"] == "ВОПРОС"


def test_parse_no_json_returns_none():
    raw = "Просто текст без JSON"
    result = parse_json(raw)
    assert result is None


def test_parse_invalid_json_returns_none():
    raw = '{"category": "ЗАКАЗ", broken}'
    result = parse_json(raw)
    assert result is None


def test_fill_template_with_entities():
    result = _fill_template("Здравствуйте, {{name}}!", {"name": "Иван"})
    assert result == "Здравствуйте, Иван!"


def test_fill_template_missing_key():
    result = _fill_template("{{unknown}}", {"name": "Иван"})
    assert "{{unknown}}" in result


def test_fill_template_with_spaces():
    result = _fill_template("{{ name }}", {"name": "Тест"})
    assert result == "Тест"


def test_fill_template_multiple_vars():
    result = _fill_template(
        "{{name}}, ваш заказ №{{order}}",
        {"name": "Иван", "order_id": "123"},
    )
    assert "Иван" in result
    assert "123" in result
