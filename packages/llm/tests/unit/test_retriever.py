from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai_mini_box_llm.rag.retriever import Retriever


class _MockEmbedModel:
    def __init__(self):
        self.available = True

    def embed(self, text: str) -> list[float] | None:
        if not text.strip():
            return None
        if text == "fail":
            return None
        return [0.1, 0.2, 0.3]


class _MockStore:
    def __init__(self):
        self.available = True
        self._dim = 3
        self._index_path = "index.faiss"
        self.data: list[tuple[str, list[float], dict]] = []

    def add(self, text: str, vec: list[float], metadata: dict | None = None):
        self.data.append((text, vec, metadata or {}))

    def search(self, vec: list[float], top_k: int = 3, threshold: float = 0.0) -> list[tuple[str, float, dict]]:
        return [("result", 0.95, {"category": "test"})]

    def load(self):
        pass

    def save(self):
        pass


class TestRetriever:
    def test_available_when_both_available(self):
        r = Retriever(_MockEmbedModel(), _MockStore())
        assert r.available

    def test_not_available_when_embed_unavailable(self):
        embed = _MockEmbedModel()
        embed.available = False
        r = Retriever(embed, _MockStore())
        assert not r.available

    def test_not_available_when_store_unavailable(self):
        store = _MockStore()
        store.available = False
        r = Retriever(_MockEmbedModel(), store)
        assert not r.available

    def test_retrieve_returns_results(self):
        r = Retriever(_MockEmbedModel(), _MockStore())
        results = r.retrieve("hello")
        assert len(results) == 1
        assert results[0][0] == "result"
        assert results[0][1] == 0.95

    def test_retrieve_empty_when_not_available(self):
        embed = _MockEmbedModel()
        embed.available = False
        r = Retriever(embed, _MockStore())
        assert r.retrieve("hello") == []

    def test_retrieve_empty_text(self):
        r = Retriever(_MockEmbedModel(), _MockStore())
        assert r.retrieve("") == []
        assert r.retrieve("   ") == []

    def test_retrieve_empty_when_embed_fails(self):
        r = Retriever(_MockEmbedModel(), _MockStore())
        assert r.retrieve("fail") == []

    def test_add_successful_reply(self):
        store = _MockStore()
        r = Retriever(_MockEmbedModel(), store)
        r.add_successful_reply("question?", "answer!", "support")
        assert len(store.data) == 1
        text, vec, meta = store.data[0]
        assert text == "question?"
        assert meta["answer"] == "answer!"
        assert meta["category"] == "support"

    def test_add_successful_reply_when_not_available(self):
        embed = _MockEmbedModel()
        embed.available = False
        store = _MockStore()
        r = Retriever(embed, store)
        r.add_successful_reply("q", "a", "cat")
        assert len(store.data) == 0

    def test_add_successful_reply_when_embed_fails(self):
        store = _MockStore()
        r = Retriever(_MockEmbedModel(), store)
        r.add_successful_reply("fail", "a", "cat")
        assert len(store.data) == 0

    def test_rebuild_index_empty_texts(self):
        r = Retriever(_MockEmbedModel(), _MockStore())
        assert r.rebuild_index([], []) == 0

    def test_rebuild_index_when_not_available(self):
        embed = _MockEmbedModel()
        embed.available = False
        r = Retriever(embed, _MockStore())
        assert r.rebuild_index(["hello"], [{"k": "v"}]) == 0

    def test_rebuild_index_zero_embeddings(self, tmp_path):
        store = _MockStore()
        store._index_path = str(tmp_path / "test.faiss")
        r = Retriever(_MockEmbedModel(), store)
        assert r.rebuild_index(["fail"], [{"k": "v"}]) == 0

    def test_rebuild_index_swaps_store(self, tmp_path):
        class TrackedStore(_MockStore):
            def __init__(self):
                super().__init__()
                self._index_path = str(tmp_path / "rag.faiss")
                self.load_called = False

            def load(self):
                self.load_called = True

            def save(self):
                pass

        embed = _MockEmbedModel()
        store = TrackedStore()
        r = Retriever(embed, store)
        count = r.rebuild_index(["hello", "world"], [{"a": 1}, {"b": 2}])
        assert count == 2
        assert r._store is not store
