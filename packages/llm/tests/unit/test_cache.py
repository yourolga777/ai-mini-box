from __future__ import annotations

import time
from threading import Thread

from ai_mini_box_llm.cache import ResponseCache


class TestResponseCache:
    def setup_method(self):
        self.cache = ResponseCache(maxsize=10, ttl_seconds=3600)

    def test_get_miss(self):
        assert self.cache.get("hello") is None

    def test_set_and_get(self):
        result = {"category": "ВОПРОС", "confidence": 0.9}
        self.cache.set("hello", result)
        cached = self.cache.get("hello")
        assert cached is not None
        assert cached["category"] == "ВОПРОС"

    def test_ttl_expiry(self):
        cache = ResponseCache(maxsize=10, ttl_seconds=0)
        cache.set("test", {"x": 1})
        time.sleep(0.01)
        assert cache.get("test") is None

    def test_lru_eviction(self):
        cache = ResponseCache(maxsize=3, ttl_seconds=3600)
        for i in range(5):
            cache.set(f"msg{i}", {"id": i})
        stats = cache.stats()
        assert stats["size"] <= 3

    def test_invalidate(self):
        self.cache.set("a", {"cat": "x"}, template_id="t1")
        self.cache.set("b", {"cat": "y"})
        self.cache.invalidate("t1")
        assert self.cache.get("a") is None
        assert self.cache.get("b") is not None

    def test_stats(self):
        self.cache.set("hello", {"cat": "q"})
        self.cache.get("hello")
        self.cache.get("miss")
        stats = self.cache.stats()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["size"] == 1

    def test_same_key_updates_not_duplicate(self):
        self.cache.set("test", {"v": 1})
        self.cache.set("test", {"v": 2})
        assert self.cache.stats()["size"] == 1
