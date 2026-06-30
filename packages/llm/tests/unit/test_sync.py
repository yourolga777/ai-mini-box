from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_mini_box_llm.models import Template
from ai_mini_box_llm.templates.sync import SystemTemplateSync


class _MockSession:
    def __init__(self):
        self.committed = False
        self._storage: dict[str, list[Any]] = {"templates": []}
        self._flushed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query):
        return _MockResult(self._storage["templates"])

    def add(self, obj):
        if obj not in self._storage["templates"]:
            self._storage["templates"].append(obj)

    def flush(self):
        self._flushed = True

    def close(self):
        pass


class _MockResult:
    def __init__(self, items: list):
        self._items = items

    def scalars(self):
        return _MockScalars(self._items)


class _MockScalars:
    def __init__(self, items: list):
        self._items = items

    def all(self):
        return self._items


def _make_db(initial: list[Template] | None = None):
    session = _MockSession()
    if initial:
        session._storage["templates"] = list(initial)
    calls = []

    def factory():
        calls.append(1)
        return session

    return factory, session, calls


def _make_template(slug: str, text: str = "Hello", version: int = 1, is_archived: int = 0, is_active: int = 1):
    t = Template(
        scope="system",
        category="general",
        name=slug,
        slug=slug,
        text=text,
        is_archived=is_archived,
        is_active=is_active,
    )
    t.version = version
    t.triggers = []
    return t


def _write_config(path: Path, templates: dict):
    config = {"templates": {"system": templates}}
    path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")


class TestSystemTemplateSync:
    def test_no_config_file(self, tmp_path: Path):
        config_path = tmp_path / "nonexistent.json"
        db_factory, _, calls = _make_db()
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()
        assert len(calls) == 0

    def test_empty_config(self, tmp_path: Path):
        config_path = tmp_path / "empty.json"
        _write_config(config_path, {})
        db_factory, _, calls = _make_db()
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()
        assert len(calls) == 0

    def test_broken_json(self, tmp_path: Path):
        config_path = tmp_path / "broken.json"
        config_path.write_text("not json", encoding="utf-8")
        db_factory, _, calls = _make_db()
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()
        assert len(calls) == 0

    def test_creates_new_templates(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        _write_config(config_path, {
            "welcome": {
                "text": "Добро пожаловать!",
                "category": "greeting",
                "triggers": ["hello", "hi"],
                "name": "Welcome",
            },
            "bye": {
                "text": "До свидания!",
                "category": "farewell",
            },
        })
        db_factory, session, _ = _make_db()
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()

        assert len(session._storage["templates"]) == 2
        slugs = {t.slug for t in session._storage["templates"]}
        assert slugs == {"welcome", "bye"}

        welcome = next(t for t in session._storage["templates"] if t.slug == "welcome")
        assert welcome.text == "Добро пожаловать!"
        assert welcome.category == "greeting"
        assert welcome.triggers == ["hello", "hi"]
        assert welcome.name == "Welcome"

    def test_updates_existing_template(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        _write_config(config_path, {
            "greeting": {
                "text": "New text!",
                "category": "general",
            },
        })
        existing = _make_template("greeting", text="Old text", version=1)
        db_factory, session, _ = _make_db(initial=[existing])
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()

        assert len(session._storage["templates"]) == 1
        t = session._storage["templates"][0]
        assert t.text == "New text!"
        assert t.version == 2

    def test_skips_unchanged_template(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        _write_config(config_path, {
            "greeting": {
                "text": "Same text",
                "category": "general",
            },
        })
        existing = _make_template("greeting", text="Same text", version=1)
        db_factory, session, _ = _make_db(initial=[existing])
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()

        t = session._storage["templates"][0]
        assert t.version == 1

    def test_archives_removed_template(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        _write_config(config_path, {
            "current": {"text": "Still here", "category": "general"},
        })
        existing_current = _make_template("current", text="Still here", version=1)
        existing_old = _make_template("old-greeting", text="Old", version=1)
        db_factory, session, _ = _make_db(initial=[existing_current, existing_old])
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()

        t_old = next(t for t in session._storage["templates"] if t.slug == "old-greeting")
        assert t_old.is_archived == 1
        assert t_old.is_active == 0

    def test_skips_already_archived(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        _write_config(config_path, {
            "current": {"text": "Still here", "category": "general"},
        })
        existing_current = _make_template("current", text="Still here", version=1)
        existing_archived = _make_template("old", text="Old", version=1, is_archived=1, is_active=0)
        db_factory, session, _ = _make_db(initial=[existing_current, existing_archived])
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()

        t = next(t for t in session._storage["templates"] if t.slug == "old")
        assert t.is_archived == 1

    def test_flush_called(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        _write_config(config_path, {
            "t": {"text": "Hi", "category": "general"},
        })
        db_factory, session, _ = _make_db()
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()
        assert session._flushed

    def test_empty_config_no_flush(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        _write_config(config_path, {})
        db_factory, session, _ = _make_db()
        sync = SystemTemplateSync(db_factory, config_path=str(config_path))
        sync.sync_on_startup()
        assert not session._flushed
