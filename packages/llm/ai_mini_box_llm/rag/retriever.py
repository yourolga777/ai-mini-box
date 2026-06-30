from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from loguru import logger

from .embeddings import EmbeddingModel
from .vector_store import FaissVectorStore


class Retriever:
    def __init__(self, embed_model: EmbeddingModel, store: FaissVectorStore):
        self._embed = embed_model
        self._store = store

    @property
    def available(self) -> bool:
        return self._embed.available and self._store.available

    def retrieve(self, text: str, top_k: int = 3) -> list[tuple[str, float, dict[str, Any]]]:
        if not self.available or not text.strip():
            return []
        vec = self._embed.embed(text)
        if not vec:
            return []
        return self._store.search(vec, top_k=top_k)

    def add_successful_reply(self, question: str, answer: str, category: str) -> None:
        if not self.available:
            return
        vec = self._embed.embed(question)
        if not vec:
            return
        self._store.add(question, vec, {"answer": answer, "category": category})
        logger.info("RAG: added successful reply for '{}'", question[:60])

    def rebuild_index(self, texts: list[str], metadatas: list[dict[str, Any]]) -> int:
        if not self.available or not texts:
            return 0
        main_path = Path(self._store._index_path)
        tmp_faiss = main_path.parent / f"{main_path.name}.tmp"
        new_store = FaissVectorStore(dim=self._store._dim, index_path=str(tmp_faiss))
        count = 0
        for text, meta in zip(texts, metadatas or []):
            vec = self._embed.embed(text)
            if vec:
                new_store.add(text, vec, meta)
                count += 1
        if count == 0:
            Path(tmp_faiss).unlink(missing_ok=True)
            Path(str(tmp_faiss) + ".json").unlink(missing_ok=True)
            return 0
        new_store.save()
        shutil.move(str(tmp_faiss), str(main_path))
        tmp_meta = str(tmp_faiss) + ".json"
        main_meta = str(main_path) + ".json"
        if Path(tmp_meta).exists():
            shutil.move(tmp_meta, main_meta)
        del new_store
        self._store = FaissVectorStore(dim=self._store._dim, index_path=str(main_path))
        self._store.load()
        logger.info("RAG index rebuilt via COW: {} entries", count)
        return count
