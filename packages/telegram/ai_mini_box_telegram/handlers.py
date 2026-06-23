from sqlalchemy.orm import Session

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Contact, Message, MessageSource, Topic


def process_update(
    update: dict,
    session: Session,
    allowed_chat_ids: list[int] | None = None,
) -> bool:
    if "message" not in update:
        return False

    message_data = update["message"]
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

    repos.messages.add(
        Message(
            source=MessageSource.TELEGRAM,
            external_id=str(update_id),
            chat_id=str(chat_id),
            contact_id=contact.id,
            text=text,
            topic=Topic.OTHER,
        )
    )

    return True
