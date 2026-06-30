from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_mini_box_llm.rag.embeddings import EmbeddingModel
from ai_mini_box_llm.rag.vector_store import FaissVectorStore


class TestEmbeddingModel:
    def test_not_available_when_no_session(self):
        model = EmbeddingModel()
        model._session = None
        assert not model.available
        assert model.embed("test") == []

    def test_embed_batch_empty(self):
        model = EmbeddingModel()
        model._session = None
        assert model.embed_batch([]) == []


class TestFaissVectorStore:
    def test_add_and_search(self, tmp_path: Path):
        store = FaissVectorStore(dim=3, index_path=str(tmp_path / "test.faiss"))
        if not store.available:
            pytest.skip("FAISS not available")
        store.add("hello", [1.0, 0.0, 0.0], {"id": 1})
        store.add("world", [0.0, 1.0, 0.0], {"id": 2})
        results = store.search([1.0, 0.0, 0.0], top_k=1, threshold=0.0)
        assert len(results) >= 1
        assert results[0][0] == "hello"

    def test_search_empty_store(self, tmp_path: Path):
        store = FaissVectorStore(dim=3, index_path=str(tmp_path / "empty.faiss"))
        if not store.available:
            pytest.skip("FAISS not available")
        assert store.search([1.0, 0.0, 0.0]) == []

    def test_search_empty_query(self, tmp_path: Path):
        store = FaissVectorStore(dim=3, index_path=str(tmp_path / "empty2.faiss"))
        assert store.search([]) == []

    def test_save_and_load(self, tmp_path: Path):
        index_path = str(tmp_path / "rag.faiss")
        store = FaissVectorStore(dim=3, index_path=index_path)
        if not store.available:
            pytest.skip("FAISS not available")
        store.add("hello", [1.0, 0.0, 0.0])
        store.save()

        store2 = FaissVectorStore(dim=3, index_path=index_path)
        assert store2.load()
        assert len(store2._metadata) == 1

    def test_load_nonexistent(self):
        store = FaissVectorStore(dim=3, index_path="nonexistent.faiss")
        assert not store.load()

    def test_threshold_filters_results(self, tmp_path: Path):
        store = FaissVectorStore(dim=3, index_path=str(tmp_path / "threshold.faiss"))
        if not store.available:
            pytest.skip("FAISS not available")
        store.add("a", [1.0, 0.0, 0.0])
        store.add("b", [0.0, 0.0, 1.0])
        results = store.search([0.0, 1.0, 0.0], top_k=2, threshold=0.5)
        assert len(results) == 0  # orthogonal, below threshold
