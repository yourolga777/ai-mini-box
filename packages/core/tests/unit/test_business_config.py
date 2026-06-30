from pathlib import Path

from ai_mini_box.core.models import BusinessConfig
from ai_mini_box.infrastructure.business_config import BusinessConfigManager


def test_create_default(tmp_path: Path):
    manager = BusinessConfigManager(tmp_path / "business_config.json")
    cfg = manager.load()
    assert cfg.company_name == "Название компании"
    assert cfg.work_hours == "Пн-Пт 9:00-18:00"
    assert cfg.faq == []


def test_load_save_roundtrip(tmp_path: Path):
    manager = BusinessConfigManager(tmp_path / "business_config.json")
    cfg = manager.load()
    cfg.company_name = "Магазин мебели"
    cfg.faq.append({"question": "Q?", "answer": "A!"})
    manager.save(cfg)

    loaded = manager.load()
    assert loaded.company_name == "Магазин мебели"
    assert len(loaded.faq) == 1
    assert loaded.faq[0]["question"] == "Q?"


def test_set_field(tmp_path: Path):
    manager = BusinessConfigManager(tmp_path / "business_config.json")
    manager.set("company_name", "Новое имя")
    cfg = manager.load()
    assert cfg.company_name == "Новое имя"


def test_set_unknown_key(tmp_path: Path):
    manager = BusinessConfigManager(tmp_path / "business_config.json")
    try:
        manager.set("nonexistent", "value")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Unknown" in str(e)


def test_faq_add_remove(tmp_path: Path):
    manager = BusinessConfigManager(tmp_path / "business_config.json")
    cfg = manager.load()
    cfg.faq.append({"question": "Q1", "answer": "A1"})
    cfg.faq.append({"question": "Q2", "answer": "A2"})
    manager.save(cfg)

    loaded = manager.load()
    assert len(loaded.faq) == 2

    loaded.faq.pop(0)
    manager.save(loaded)

    final = manager.load()
    assert len(final.faq) == 1
    assert final.faq[0]["question"] == "Q2"


def test_file_created_on_load(tmp_path: Path):
    path = tmp_path / "business_config.json"
    assert not path.exists()
    manager = BusinessConfigManager(path)
    manager.load()
    assert path.exists()
