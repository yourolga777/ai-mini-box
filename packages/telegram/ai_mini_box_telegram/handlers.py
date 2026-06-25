from sqlalchemy.orm import Session

from ai_mini_box.core.answer_service import auto_draft_response
from ai_mini_box.core.classifier import create_classifier
from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.extraction import extract_phone
from ai_mini_box.core.models import Contact, Message, MessageSource

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = create_classifier()
    return _classifier


_BUSINESS_FIELD = "business_message"


def process_update(
    update: dict,
    session: Session,
    allowed_chat_ids: list[int] | None = None,
) -> bool:
    message_data = update.get("message") or update.get(_BUSINESS_FIELD)
    if message_data is None:
        return False

    chat_id = message_data["chat"]["id"]

    if allowed_chat_ids and chat_id not in allowed_chat_ids:
        return False

    update_id = update["update_id"]
    text = message_data.get("text") or message_data.get("caption", "")
    repos = RepoContainer(session)

    contacts = repos.contacts.list(telegram=str(chat_id), limit=1)
    if contacts:
        contact = contacts[0]
    else:
        contact = repos.contacts.add(
            Contact(
                name=str(chat_id),
                telegram=str(chat_id),
                source=MessageSource.TELEGRAM,
            )
        )

    topic = _get_classifier().classify(text)

    from_user = message_data.get("from", {})
    extracted_phone = extract_phone(text)
    first = from_user.get("first_name", "") or ""
    last = from_user.get("last_name", "") or ""
    extracted_name = f"{first} {last}".strip()
    draft_response = auto_draft_response(text, topic, repos)

    repos.messages.add(
        Message(
            source=MessageSource.TELEGRAM,
            external_id=str(update_id),
            chat_id=str(chat_id),
            contact_id=contact.id,
            text=text,
            topic=topic,
            extracted_phone=extracted_phone,
            extracted_name=extracted_name,
            draft_response=draft_response,
        )
    )

    return True
