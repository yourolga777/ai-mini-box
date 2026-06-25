from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    def __init__(self, index_path: str = "data/llm_rag_index.json"):
        self.index_path = Path(index_path)
        self.entries: list[dict[str, Any]] = []

    def add(self, entry: dict[str, Any]) -> None:
        self.entries.append(entry)

    def search(self, query_vec: list[float], top_k: int = 3) -> list[dict[str, Any]]:
        if not query_vec or not self.entries:
            return []
        scored = []
        for entry in self.entries:
            vec = entry.get("embedding", [])
            if vec:
                score = cosine_similarity(query_vec, vec)
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for score, entry in scored[:top_k] if score > 0.5]

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump({"entries": self.entries}, f, ensure_ascii=False, default=str)

    def load(self) -> None:
        if not self.index_path.exists():
            self.entries = []
            return
        with open(self.index_path, encoding="utf-8") as f:
            data = json.load(f)
        self.entries = data.get("entries", [])
