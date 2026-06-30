from loguru import logger
from sqlalchemy.orm import Session

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.extraction import extract_phone
from ai_mini_box.core.models import Contact, Message, MessageSource, Topic
from ai_mini_box.core.services.registry import get_service


def _category_to_topic(category: str) -> Topic | None:
    mapping = {
        "ЗАКАЗ": Topic.ORDER,
        "ЖАЛОБА": Topic.COMPLAINT,
        "ФЛУД": Topic.OTHER,
    }
    return mapping.get(category)


def get_chat_history(repos: RepoContainer, chat_id: str, limit: int = 5) -> list[dict]:
    messages = repos.messages.list_by_chat(chat_id, limit=limit)
    history = []
    for msg in reversed(messages):
        if msg.sent_response and msg.auto_reply_text:
            history.append({"role": "assistant", "text": msg.auto_reply_text})
        else:
            history.append({"role": "user", "text": msg.text})
    return history


def process_update(
    update: dict,
    session,
    allowed_chat_ids: list[int] | None = None,
) -> bool:
    message_data = update.get("message") or update.get("business_message")
    if message_data is None:
        return False

    chat_id = message_data["chat"]["id"]
    if allowed_chat_ids and chat_id not in allowed_chat_ids:
        return False

    repos = RepoContainer(session)

    text = message_data.get("text") or message_data.get("caption", "")
    from_user = message_data.get("from", {})
    first = from_user.get("first_name", "") or ""
    last = from_user.get("last_name", "") or ""
    user_name = f"{first} {last}".strip() or str(chat_id)

    contacts = repos.contacts.list(telegram=str(chat_id), limit=1)
    if contacts:
        contact = contacts[0]
    else:
        contact = repos.contacts.add(
            Contact(
                name=user_name,
                telegram=str(chat_id),
                source=MessageSource.TELEGRAM,
            )
        )

    extracted_phone = extract_phone(text)
    msg = repos.messages.add(
        Message(
            source=MessageSource.TELEGRAM,
            external_id=str(update.get("update_id", "")),
            chat_id=str(chat_id),
            contact_id=contact.id,
            text=text,
            extracted_phone=extracted_phone,
            extracted_name=user_name,
        )
    )

    try:
        from ai_mini_box_llm.pipeline import ProcessingContext
    except ImportError:
        logger.warning("LLM pipeline not available, skipping enrichment")
        return True

    pipeline = get_service("llm")
    if pipeline is None:
        logger.warning("LLM pipeline not available, skipping enrichment")
        return True

    try:
        history = get_chat_history(repos, str(chat_id))
        result = pipeline.process(text, ProcessingContext(
            text=text,
            history=history,
            user_name=user_name,
            category=None,
        ))
    except Exception:
        logger.exception("Pipeline processing failed, saving message without enrichment")
        return True

    msg.category = result.category
    msg.subcategory = None
    msg.need_human = result.need_human
    msg.auto_replied = (result.reply_text is not None and not result.need_human)
    msg.auto_reply_text = result.reply_text
    msg.operator_context = f"Категория: {result.category} ({result.confidence:.0%})"
    msg.topic = _category_to_topic(result.category)

    repos.messages.update(msg)

    if result.is_order:
        try:
            from ai_mini_box.core.services.order_service import OrderService
            order_svc = OrderService(repos)
            order_svc.create_from_message(
                message_id=msg.id,
                contact_id=contact.id,
                notes=text,
            )
        except Exception:
            logger.exception("Failed to create order from message")

    if msg.auto_replied and result.reply_text:
        tg = get_service("telegram")
        if tg:
            try:
                tg.send_message(chat_id, result.reply_text)
                msg.sent_response = True
                repos.messages.update(msg)
                logger.info("Auto-reply sent to chat {}: {}", chat_id, result.reply_text[:60])
            except Exception:
                logger.exception("Failed to send auto-reply to chat {}", chat_id)

    return True
