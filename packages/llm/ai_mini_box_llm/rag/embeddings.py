from __future__ import annotations

from typing import Optional

from ..providers.base import BaseLLMProvider


def get_embedding(provider: BaseLLMProvider, text: str) -> list[float]:
    """Get embedding vector for text via the provider."""
    return provider.embed(text)


def get_embeddings_batch(provider: BaseLLMProvider, texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts."""
    return [get_embedding(provider, t) for t in texts]
