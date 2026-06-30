from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

from loguru import logger
from sqlalchemy import select

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Contact, Message, Order
from ai_mini_box.core.services.registry import get_service


@dataclass
class AutoProcessResult:
    contact_updated: bool = False
    task_created: bool = False
    task_title: str | None = None
    folder_assigned: bool = False
    order_created: bool = False


class AutoProcessor:
    def __init__(self, repos: RepoContainer | None = None):
        self._repos = repos

    def _get_repos(self):
        if self._repos is not None:
            return self._repos
        from ai_mini_box.infrastructure.database import get_session
        from ai_mini_box.core.container import RepoContainer as _RepoContainer
        return _RepoContainer(get_session())

    def process(self, message: Message, contact: Contact, repos: RepoContainer | None = None) -> AutoProcessResult:
        result = AutoProcessResult()
        if repos is None:
            repos = self._get_repos()

        pipeline = get_service("llm")
        if pipeline is None or not message.text:
            return result

        from ai_mini_box_llm.pipeline import ProcessingContext

        p_result = pipeline.process(message.text, ProcessingContext(
            text=message.text,
            history=[],
            user_name=message.extracted_name or "",
            category=None,
        ))

        if p_result.entities.get("phone") and contact:
            contact.phone = p_result.entities["phone"]
            repos.contacts.update(contact)
            result.contact_updated = True
            logger.info("AutoProcessor: updated contact {} phone → {}", contact.id, p_result.entities["phone"])

        if message.extracted_name and contact and contact.name and contact.name.isdigit():
            contact.name = message.extracted_name
            repos.contacts.update(contact)
            result.contact_updated = True
            logger.info("AutoProcessor: updated contact {} name → {}", contact.id, message.extracted_name)

        date_val = p_result.entities.get("date")
        time_val = p_result.entities.get("time")
        if date_val:
            from datetime import date as _date
            try:
                parts = str(date_val).split("-")
                due_date = _date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                due_date = _date.today()
                logger.warning("AutoProcessor: could not parse date {!r}, using today", date_val)

            from ai_mini_box.core.models import Task
            title = f"Задача из сообщения: {message.text[:80]}"
            repos.tasks.add(Task(
                title=title,
                due_date=due_date,
                due_time=time_val,
                contact_id=contact.id,
                priority="medium",
            ))
            result.task_created = True
            result.task_title = title
            logger.info("AutoProcessor: created task for contact {} due {}", contact.id, due_date)

        if p_result.is_order:
            order = Order(
                contact_id=message.contact_id,
                source_message_id=message.id,
                notes=message.text,
                status="new",
            )
            created = repos.orders.add(order)
            message.extracted_order_id = created.id
            repos.messages.update(message)
            result.order_created = True
            logger.info("AutoProcessor: created order #{} from message #{}", created.id, message.id)

        folder_assigned = self._assign_llm_folder(repos, message, p_result.category)
        if folder_assigned:
            result.folder_assigned = True

        return result

    def _assign_llm_folder(self, repos, message: Message, category: str) -> bool:
        try:
            from ai_mini_box_llm.models import MessageCategory, MessageCategoryAssignment
        except ImportError:
            return False

        try:
            cats = repos._session.execute(select(MessageCategory)).scalars().all()
            if not cats:
                return False

            best = None
            for c in cats:
                if c.name.lower() in category.lower() or category.lower() in c.name.lower():
                    best = c
                    break
            if best is None:
                for c in cats:
                    if c.name == "Другое":
                        best = c
                        break
            if best is None:
                return False

            existing = repos._session.execute(
                select(MessageCategoryAssignment).where(
                    MessageCategoryAssignment.message_id == message.id,
                    MessageCategoryAssignment.category_id == best.id,
                )
            ).scalar_one_or_none()
            if not existing:
                repos._session.add(MessageCategoryAssignment(
                    message_id=message.id, category_id=best.id, assigned_by="llm",
                ))
                repos._session.flush()
                logger.info("LLM folder assigned: msg={} folder={}", message.id, best.name)
                return True
        except Exception:
            logger.exception("LLM folder assignment failed")
        return False

    def process_all(self, limit: int = 50) -> tuple[int, int]:
        from ai_mini_box.infrastructure.database import get_db
        from ai_mini_box_llm.models import MessageCategoryAssignment

        repos = self._get_repos()
        actual_limit = 10**9 if limit <= 0 else limit
        all_msgs = repos.messages.list(limit=actual_limit)
        processed = 0
        assigned = 0

        for msg in all_msgs:
            if not msg.text:
                continue

            with get_db() as session:
                existing = session.execute(
                    select(MessageCategoryAssignment).where(
                        MessageCategoryAssignment.message_id == msg.id
                    )
                ).scalar_one_or_none()
                if existing:
                    continue

            contact = None
            if msg.contact_id:
                try:
                    contact = repos.contacts.get_by_id(msg.contact_id)
                except Exception:
                    pass

            try:
                with get_db() as per_msg_db:
                    per_msg_repos = RepoContainer(per_msg_db)
                    per_msg_contact = contact
                    if msg.contact_id and per_msg_contact is not None:
                        try:
                            per_msg_contact = per_msg_repos.contacts.get_by_id(msg.contact_id)
                        except Exception:
                            pass
                    result = self.process(msg, per_msg_contact or Message(), repos=per_msg_repos)
                    processed += 1
                    if result.folder_assigned:
                        assigned += 1
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    logger.warning("AutoProcessor: db locked on msg {}, skipping", msg.id)
                    continue
                raise

        repos._session.close()
        return (processed, assigned)
