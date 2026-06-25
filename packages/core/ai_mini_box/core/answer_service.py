from typing import Optional

from ai_mini_box.core.models import Topic
from ai_mini_box.core.container import RepoContainer


def auto_draft_response(text: str, topic: Topic, repos: RepoContainer) -> Optional[str]:
    """
    Layer 1: KnowledgeBase keyword matching — MVP
    Layer 2: LLM-generation — future (placeholder)

    Returns answer_text from the best-matching KB entry, or None.
    """
    matches = repos.kb.find_matching(text, topic)
    return matches[0].answer_text if matches else None
