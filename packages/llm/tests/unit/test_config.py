import json
from pathlib import Path

from ai_mini_box_llm.config import LlmConfig


def test_load_creates_defaults(tmp_path: Path):
    path = tmp_path / "llm_config.json"
    cfg = LlmConfig.load(path)
    assert cfg.provider == "local"
    assert cfg.n_ctx == 4096
    assert cfg.n_threads == 4
    assert cfg.rag_enabled is False


def test_load_existing_file(tmp_path: Path):
    path = tmp_path / "llm_config.json"
    data = {"provider": "remote", "api_key": "sk-test", "n_ctx": 2048}
    path.write_text(json.dumps(data), encoding="utf-8")
    cfg = LlmConfig.load(path)
    assert cfg.provider == "remote"
    assert cfg.api_key == "sk-test"
    assert cfg.n_ctx == 2048
    assert cfg.n_threads == 4


def test_load_ignores_unknown_fields(tmp_path: Path):
    path = tmp_path / "llm_config.json"
    data = {"provider": "local", "unknown_field": "should_be_ignored"}
    path.write_text(json.dumps(data), encoding="utf-8")
    cfg = LlmConfig.load(path)
    assert cfg.provider == "local"
    assert not hasattr(cfg, "unknown_field")


def test_save_and_reload(tmp_path: Path):
    path = tmp_path / "llm_config.json"
    cfg = LlmConfig(provider="remote", model_name="gpt-4", api_key="sk-test")
    cfg.save(path)
    assert path.exists()

    loaded = LlmConfig.load(path)
    assert loaded.provider == "remote"
    assert loaded.model_name == "gpt-4"
    assert loaded.api_key == "sk-test"
