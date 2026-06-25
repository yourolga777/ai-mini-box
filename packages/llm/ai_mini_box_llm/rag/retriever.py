from __future__ import annotations

from typing import Optional

from loguru import logger

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import KnowledgeBaseItem
from ai_mini_box.infrastructure.database import get_db

from ..prompt import RAG_CONTEXT_TEMPLATE
from ..providers.base import BaseLLMProvider
from .embeddings import get_embedding
from .vector_store import VectorStore


def rebuild_index(provider: BaseLLMProvider, index_path: str = "data/llm_rag_index.json") -> int:
    """Reindex all KnowledgeBase items from the database."""
    store = VectorStore(index_path)
    store.entries = []

    with get_db() as session:
        repos = RepoContainer(session)
        all_items = repos.kb.list()
        if not all_items:
            logger.info("No KB items to index")
            store.save()
            return 0

        texts = [item.answer_text for item in all_items]
        logger.info("Generating embeddings for {} KB items...", len(texts))

        for item in all_items:
            embedding = get_embedding(provider, item.answer_text)
            store.add({
                "kb_id": item.id,
                "topic": item.topic.value if item.topic else None,
                "question_keywords": item.question_keywords,
                "answer_text": item.answer_text,
                "embedding": embedding,
            })

    store.save()
    logger.info("Index saved with {} entries", len(store.entries))
    return len(store.entries)


def retrieve_context(
    provider: BaseLLMProvider,
    text: str,
    top_k: int = 3,
    index_path: str = "data/llm_rag_index.json",
) -> str:
    """Retrieve relevant KB context for a given text."""
    store = VectorStore(index_path)
    store.load()

    if not store.entries:
        return ""

    query_vec = get_embedding(provider, text)
    if not query_vec:
        return ""

    results = store.search(query_vec, top_k=top_k)
    if not results:
        return ""

    context_parts = []
    for i, entry in enumerate(results, 1):
        context_parts.append(f"{i}. {entry['answer_text']}")

    return RAG_CONTEXT_TEMPLATE.format(context="\n".join(context_parts))
