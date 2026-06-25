import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_mini_box_llm.rag.embeddings import get_embedding, get_embeddings_batch
from ai_mini_box_llm.rag.vector_store import VectorStore, cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert cosine_similarity([1, 0, 0], [-1, 0, 0]) == pytest.approx(-1.0)

    def test_zero_vector(self):
        assert cosine_similarity([0, 0, 0], [1, 0, 0]) == 0.0


class TestVectorStore:
    def test_add_and_search(self):
        store = VectorStore(index_path=":memory:")
        store.add({"id": 1, "text": "hello", "embedding": [1, 0, 0]})
        store.add({"id": 2, "text": "world", "embedding": [0, 1, 0]})

        results = store.search([1, 0, 0], top_k=1)
        assert len(results) == 1
        assert results[0]["id"] == 1

    def test_search_empty_store(self):
        store = VectorStore(index_path=":memory:")
        assert store.search([1, 0, 0]) == []

    def test_search_empty_query(self):
        store = VectorStore(index_path=":memory:")
        store.add({"id": 1, "text": "hello", "embedding": [1, 0, 0]})
        assert store.search([], top_k=1) == []

    def test_save_and_load(self, tmp_path: Path):
        index_path = str(tmp_path / "index.json")
        store = VectorStore(index_path=index_path)
        store.add({"id": 1, "text": "hello", "embedding": [1, 0, 0]})
        store.save()

        store2 = VectorStore(index_path=index_path)
        store2.load()
        assert len(store2.entries) == 1
        assert store2.entries[0]["id"] == 1

    def test_load_nonexistent(self):
        store = VectorStore(index_path="nonexistent.json")
        store.load()
        assert store.entries == []


class TestEmbeddings:
    def test_get_embedding(self):
        provider = MagicMock()
        provider.embed.return_value = [0.1, 0.2, 0.3]
        result = get_embedding(provider, "test")
        assert result == [0.1, 0.2, 0.3]

    def test_get_embeddings_batch(self):
        provider = MagicMock()
        provider.embed.side_effect = [[0.1], [0.2]]
        result = get_embeddings_batch(provider, ["a", "b"])
        assert result == [[0.1], [0.2]]
