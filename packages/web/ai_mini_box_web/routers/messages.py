from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import KnowledgeBaseItem, Message, Topic
from ai_mini_box_web.dependencies import get_repos


class ReplyRequest(BaseModel):
    text: str
    save_to_kb: bool = False

router = APIRouter()


@router.get("")
def list_messages(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    topic: Topic | None = Query(None),
    search: str | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
):
    if search:
        items = repos.messages.search(search, topic=topic.value if topic else None)
        return [m.model_dump() for m in items]
    filters = {}
    if topic:
        filters["topic"] = topic
    items = repos.messages.list(limit=limit, offset=offset, **filters)
    return [m.model_dump() for m in items]


@router.get("/{item_id}")
def get_message(item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.messages.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return item.model_dump()


@router.post("/{item_id}/reply")
def reply_to_message(item_id: int, body: ReplyRequest, repos: RepoContainer = Depends(get_repos)):
    msg = repos.messages.get_by_id(item_id)
    if msg is None:
        raise HTTPException(404)

    msg.draft_response = body.text
    msg.sent_response = True
    repos.messages.update(msg)

    if body.save_to_kb:
        words = [w.lower().strip(".,!?()") for w in msg.text.split() if len(w) > 3]
        keywords = list(dict.fromkeys(words))[:8]
        repos.kb.add(KnowledgeBaseItem(
            topic=msg.topic,
            question_keywords=keywords,
            answer_text=body.text,
        ))

    if msg.source.value == "telegram" and msg.chat_id:
        from ai_mini_box.infrastructure.config import JsonConfigManager
        from ai_mini_box_telegram.bot import TelegramBot
        raw = JsonConfigManager().load()
        token = raw.telegram_token
        if token:
            TelegramBot(token).send_message(int(msg.chat_id), body.text)

    return msg.model_dump()
