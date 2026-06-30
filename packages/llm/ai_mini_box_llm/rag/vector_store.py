from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

try:
    import faiss
except ImportError:
    faiss = None


class FaissVectorStore:
    def __init__(self, dim: int = 384, index_path: str = "data/rag_index.faiss"):
        self._dim = dim
        self._index_path = Path(index_path)
        self._metadata: list[dict[str, Any]] = []
        if faiss is not None:
            self._index = faiss.IndexFlatIP(dim)
        else:
            self._index = None

    @property
    def available(self) -> bool:
        return faiss is not None and self._index is not None

    def add(self, text: str, embedding: list[float], metadata: dict[str, Any] | None = None) -> None:
        if not self.available or not embedding:
            return
        vec = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vec)
        self._index.add(vec)
        entry = {"text": text, **(metadata or {})}
        self._metadata.append(entry)

    def search(self, query_vec: list[float], top_k: int = 3, threshold: float = 0.75) -> list[tuple[str, float, dict[str, Any]]]:
        if not self.available or not query_vec or self._index.ntotal == 0:
            return []
        vec = np.array([query_vec], dtype=np.float32)
        faiss.normalize_L2(vec)
        scores, indices = self._index.search(vec, min(top_k, self._index.ntotal))
        results: list[tuple[str, float, dict[str, Any]]] = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= threshold and 0 <= idx < len(self._metadata):
                meta = dict(self._metadata[int(idx)])
                text = meta.pop("text", "")
                results.append((text, float(score), meta))
        return results

    def save(self) -> None:
        if not self.available:
            return
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_faiss = tempfile.NamedTemporaryFile(delete=False, suffix=".faiss", dir=self._index_path.parent)
        tmp_meta = tmp_faiss.name + ".json"
        try:
            faiss.write_index(self._index, tmp_faiss.name)
            with open(tmp_meta, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, ensure_ascii=False, default=str)
            tmp_faiss.close()
            import shutil
            shutil.move(tmp_faiss.name, str(self._index_path))
            shutil.move(tmp_meta, str(self._index_path) + ".json")
        except Exception:
            Path(tmp_faiss.name).unlink(missing_ok=True)
            Path(tmp_meta).unlink(missing_ok=True)
            raise

    def load(self) -> bool:
        if faiss is None:
            return False
        index_file = self._index_path
        meta_file = self._index_path.with_name(self._index_path.name + ".json")
        if not index_file.exists() or not meta_file.exists():
            return False
        try:
            self._index = faiss.read_index(str(index_file))
            with open(meta_file, encoding="utf-8") as f:
                self._metadata = json.load(f)
            return True
        except Exception as e:
            logger.warning("Failed to load FAISS index: {}", e)
            return False
