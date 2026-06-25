from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class LlmConfig(BaseModel):
    provider: str = "local"
    model_path: str = "data/models/Phi-3-mini-q4.gguf"
    n_ctx: int = 4096
    n_threads: int = 4
    api_url: str = ""
    api_key: str = ""
    model_name: str = ""
    rag_enabled: bool = False
    rag_top_k: int = 3
    rag_index_path: str = "data/llm_rag_index.json"

    @classmethod
    def load(cls, path: str | Path = "data/llm_config.json") -> LlmConfig:
        path = Path(path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            cfg = cls()
            cfg.save(path)
            return cfg
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        valid_keys = cls.model_fields.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def save(self, path: str | Path = "data/llm_config.json") -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)
