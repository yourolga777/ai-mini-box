import json
from pathlib import Path
from typing import Any

from loguru import logger

from ai_mini_box.core.models import BusinessConfig


def load_business_config(path: str | Path = "data/business_config.json") -> BusinessConfig:
    p = Path(path)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return BusinessConfig(**data)
        except Exception:
            logger.exception("Failed to load business_config.json, using defaults")
    return BusinessConfig()


def save_business_config(config: BusinessConfig, path: str | Path = "data/business_config.json") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(config.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    tmp.replace(p)


class BusinessConfigManager:
    def __init__(self, path: str | Path = "data/business_config.json"):
        self.path = Path(path)

    def load(self) -> BusinessConfig:
        cfg = load_business_config(self.path)
        if not self.path.exists():
            self.save(cfg)
        return cfg

    def save(self, config: BusinessConfig) -> None:
        save_business_config(config, self.path)

    def set(self, key: str, value: Any) -> bool:
        if key not in BusinessConfig.model_fields:
            raise ValueError(f"Unknown business config key: {key}")
        cfg = self.load()
        setattr(cfg, key, value)
        self.save(cfg)
        return True
