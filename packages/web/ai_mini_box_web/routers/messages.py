from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import KnowledgeBaseItem, Message, Order, Topic
from ai_mini_box_web.dependencies import get_repos


class ReplyRequest(BaseModel):
    text: str
    save_to_kb: bool = False


class _SetContactRequest(BaseModel):
    contact_id: int


class _CreateOrderRequest(BaseModel):
    total_kopecks: int = 0
    notes: str = ""


router = APIRouter()


@router.get("")
def list_messages(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    topic: Topic | None = Query(None),
    search: str | None = Query(None),
    contact_id: int | None = Query(None),
    category_id: int | None = Query(None),
    need_human: bool | None = Query(None),
    category: str | None = Query(None),
    sort: str | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
):
    if category_id is not None:
        try:
            from ai_mini_box_llm.models import MessageCategoryAssignment as MCA
        except ImportError:
            raise HTTPException(502, detail="LLM plugin not installed")
        ids = repos._session.execute(
            select(MCA.message_id).where(MCA.category_id == category_id)
        ).scalars().all()
        if not ids:
            return []
        from ai_mini_box.infrastructure.orm_models import MessageModel
        from ai_mini_box.infrastructure.repositories.message_repo import message_from_orm
        objs = repos._session.execute(
            select(MessageModel).where(MessageModel.id.in_(ids)).limit(limit).offset(offset)
        ).scalars().all()
        return [message_from_orm(o).model_dump() for o in objs]

    if search:
        items = repos.messages.search(search, topic=topic.value if topic else None)
        return [m.model_dump() for m in items]
    filters = {}
    if topic:
        filters["topic"] = topic
    if contact_id is not None:
        filters["contact_id"] = contact_id
    if need_human is not None:
        filters["need_human"] = need_human
    if category:
        filters["category"] = category
    if sort:
        parts = sort.split(":")
        sort_field = parts[0]
        items = repos.messages.list(limit=limit, offset=offset, sort=sort_field, **filters)
    else:
        items = repos.messages.list(limit=limit, offset=offset, **filters)
    return [m.model_dump() for m in items]


@router.put("/{item_id}")
def update_message(item_id: int, data: dict, repos: RepoContainer = Depends(get_repos)):
    existing = repos.messages.get_by_id(item_id)
    if existing is None:
        raise HTTPException(404)
    updated = existing.model_copy(update=data)
    result = repos.messages.update(updated)
    return result.model_dump()


@router.put("/{item_id}/contact")
def set_message_contact(item_id: int, body: _SetContactRequest, repos: RepoContainer = Depends(get_repos)):
    msg = repos.messages.get_by_id(item_id)
    if msg is None:
        raise HTTPException(404, detail="Message not found")
    contact = repos.contacts.get_by_id(body.contact_id)
    if contact is None:
        raise HTTPException(404, detail="Contact not found")
    msg.contact_id = body.contact_id
    repos.messages.update(msg)
    return msg.model_dump()


@router.get("/{item_id}")
def get_message(item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.messages.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return item.model_dump()


@router.get("/{item_id}/categories")
def get_message_categories(item_id: int, repos: RepoContainer = Depends(get_repos)):
    msg = repos.messages.get_by_id(item_id)
    if msg is None:
        raise HTTPException(404, detail="Message not found")
    try:
        from ai_mini_box_llm.models import MessageCategory, MessageCategoryAssignment
    except ImportError:
        return []
    from ai_mini_box.infrastructure.database import get_db as _get_db
    with _get_db() as session:
        assignments = session.execute(
            select(MessageCategoryAssignment).where(MessageCategoryAssignment.message_id == item_id)
        ).scalars().all()
        result = []
        for a in assignments:
            cat = session.get(MessageCategory, a.category_id)
            if cat:
                result.append({
                    "id": cat.id,
                    "name": cat.name,
                    "description": cat.description,
                    "color": cat.color,
                    "is_system": cat.is_system,
                })
        return result


@router.get("/{item_id}/order")
def get_message_order(item_id: int, repos: RepoContainer = Depends(get_repos)):
    msg = repos.messages.get_by_id(item_id)
    if msg is None:
        raise HTTPException(404, detail="Message not found")
    if msg.extracted_order_id is None:
        return None
    order = repos.orders.get_by_id(msg.extracted_order_id)
    return order.model_dump() if order else None


@router.post("/{item_id}/create-order")
def create_message_order(item_id: int, body: _CreateOrderRequest, repos: RepoContainer = Depends(get_repos)):
    msg = repos.messages.get_by_id(item_id)
    if msg is None:
        raise HTTPException(404, detail="Message not found")
    if msg.extracted_order_id is not None:
        raise HTTPException(409, detail="Order already exists for this message")
    if msg.contact_id is None:
        raise HTTPException(400, detail="Cannot create order without a contact")

    order = Order(
        contact_id=msg.contact_id,
        source_message_id=msg.id,
        total_kopecks=body.total_kopecks,
        notes=body.notes or msg.text,
        status="new",
    )
    created = repos.orders.add(order)
    msg.extracted_order_id = created.id
    repos.messages.update(msg)
    return created.model_dump()


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


@router.post("/{item_id}/reprocess-chatbot")
def reprocess_message_chatbot(item_id: int, repos: RepoContainer = Depends(get_repos)):
    msg = repos.messages.get_by_id(item_id)
    if msg is None:
        raise HTTPException(404)

    pipeline = None
    try:
        from ai_mini_box_llm.pipeline import Pipeline, ProcessingContext
        from ai_mini_box.core.services.registry import get_service
        pipeline = get_service("llm")
    except ImportError:
        pass

    if pipeline is None:
        raise HTTPException(400, detail="LLM pipeline not available (LLM plugin not installed)")

    try:
        context = ProcessingContext(
            text=msg.text,
            history=[],
            user_name=msg.extracted_name or "",
            category=msg.category,
        )
        result = pipeline.process(msg.text, context)
    except Exception as e:
        raise HTTPException(500, detail=f"Pipeline processing failed: {e}")

    msg.category = result.category
    msg.need_human = result.need_human
    msg.auto_replied = (result.reply_text is not None and not result.need_human)
    msg.auto_reply_text = result.reply_text
    msg.operator_context = f"Категория: {result.category} ({result.confidence:.0%})"
    repos.messages.update(msg)

    return {
        "success": True,
        "category": result.category,
        "reply_to_user": result.reply_text,
        "need_human": result.need_human,
        "auto_replied": msg.auto_replied,
    }
