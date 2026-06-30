from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any


@dataclass
class CacheEntry:
    result: dict[str, Any]
    created_at: float
    template_id: str | None = None


class ResponseCache:
    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 604800):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._hit_count = 0
        self._miss_count = 0

    def _key(self, text: str) -> str:
        return sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> dict[str, Any] | None:
        key = self._key(text)
        entry = self._cache.get(key)
        if entry is None:
            self._miss_count += 1
            return None
        if time.time() - entry.created_at > self._ttl:
            del self._cache[key]
            self._miss_count += 1
            return None
        self._cache.move_to_end(key)
        self._hit_count += 1
        return entry.result

    def set(self, text: str, result: dict[str, Any], template_id: str | None = None) -> None:
        key = self._key(text)
        if key in self._cache:
            self._cache.move_to_end(key)
            return
        if len(self._cache) >= self._maxsize:
            self._cache.popitem(last=False)
        self._cache[key] = CacheEntry(result=result, created_at=time.time(), template_id=template_id)

    def invalidate(self, template_id: str) -> None:
        to_delete = [k for k, v in self._cache.items() if v.template_id == template_id]
        for k in to_delete:
            del self._cache[k]

    def stats(self) -> dict[str, Any]:
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0.0
        oldest = min((e.created_at for e in self._cache.values()), default=0)
        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_pct": round(hit_rate, 1),
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "oldest_entry_age_seconds": int(time.time() - oldest) if oldest else 0,
        }
