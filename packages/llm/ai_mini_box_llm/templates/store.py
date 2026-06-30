from __future__ import annotations

import re
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Template, TemplateUsageLog


class TemplateCreate:
    def __init__(
        self,
        scope: str,
        category: str,
        name: str,
        text: str,
        variables: list[str] | None = None,
        defaults: dict[str, str] | None = None,
        triggers: list[str] | None = None,
        confidence_min: float = 0.6,
    ):
        self.scope = scope
        self.category = category
        self.name = name
        self.text = text
        self.variables = variables or []
        self.defaults = defaults or {}
        self.triggers = triggers or []
        self.confidence_min = confidence_min


class TemplateUpdate:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


FALLBACK_TEXTS = [
    "Здравствуйте! Я передал ваш запрос специалисту. Ожидайте ответа.",
    "Здравствуйте! Ожидайте ответа, мы скоро свяжемся с вами.",
]


class TemplateStore:
    def __init__(self, db_session_factory: Callable[[], Session]):
        self._db = db_session_factory

    def get(self, template_id: str) -> Template | None:
        with self._db() as session:
            return session.get(Template, template_id)

    def list(
        self,
        scope: str | None = None,
        category: str | None = None,
        is_active: bool = True,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Template]:
        with self._db() as session:
            query = select(Template)
            if scope:
                query = query.where(Template.scope == scope)
            if category:
                query = query.where(Template.category == category)
            if is_active:
                query = query.where(Template.is_active == 1, Template.is_archived == 0)
            if search:
                query = query.where(Template.text.contains(search))
            all_ = list(session.execute(query).scalars().all())
            for t in all_:
                session.expunge(t)
            all_.sort(key=lambda t: t.success_rate, reverse=True)
            return all_[offset:offset + limit]

    def create(self, data: TemplateCreate) -> Template:
        from ..models import Template as T
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", data.name.lower()).strip("-")
        with self._db() as session:
            t = T(
                scope=data.scope,
                category=data.category,
                name=data.name,
                slug=slug,
                text=data.text,
                confidence_min=data.confidence_min,
            )
            t.variables = data.variables
            t.defaults = data.defaults
            t.triggers = data.triggers
            session.add(t)
            session.flush()
            session.refresh(t)
            session.expunge(t)
            return t

    def update(self, template_id: str, data: TemplateUpdate) -> Template | None:
        with self._db() as session:
            t = session.get(Template, template_id)
            if t is None:
                return None
            for key in ("scope", "category", "name", "text", "confidence_min", "is_active", "is_archived"):
                val = getattr(data, key, None)
                if val is not None:
                    setattr(t, key, val)
            if hasattr(data, "variables") and data.variables is not None:
                t.variables = data.variables
            if hasattr(data, "defaults") and data.defaults is not None:
                t.defaults = data.defaults
            if hasattr(data, "triggers") and data.triggers is not None:
                t.triggers = data.triggers
            t.version += 1
            session.flush()
            session.refresh(t)
            session.expunge(t)
            return t

    def delete(self, template_id: str, hard: bool = False) -> bool:
        with self._db() as session:
            t = session.get(Template, template_id)
            if t is None:
                return False
            if hard:
                session.delete(t)
            else:
                t.is_archived = 1
                t.is_active = 0
            session.flush()
            return True

    def find_best(
        self,
        category: str,
        text: str,
        entities: dict[str, Any],
        confidence: float,
        rag_result: tuple[str, float, dict[str, Any]] | None = None,
    ) -> Template | None:
        system_t = self.find_by_triggers(text)
        if system_t:
            return system_t

        business_t = self.find_by_category(category, confidence)
        if business_t:
            return business_t

        if rag_result and rag_result[1] > 0.75:
            t = Template(
                scope="learned",
                text=rag_result[0],
                category=category,
                name="RAG result",
                slug="rag-result",
            )
            t.variables = list(entities.keys())
            return t

        return self._get_fallback()

    def find_by_triggers(self, text: str) -> Template | None:
        if not text:
            return None
        with self._db() as session:
            templates = session.execute(
                select(Template).where(
                    Template.scope == "system",
                    Template.is_active == 1,
                    Template.is_archived == 0,
                )
            ).scalars().all()
            text_lower = text.lower()
            for t in templates:
                for trigger in t.triggers:
                    if trigger.lower() in text_lower:
                        return t
        return None

    def find_by_category(self, category: str, confidence: float) -> Template | None:
        with self._db() as session:
            templates = session.execute(
                select(Template).where(
                    Template.scope == "business",
                    Template.category == category,
                    Template.is_active == 1,
                    Template.is_archived == 0,
                    Template.confidence_min <= confidence,
                )
            ).scalars().all()
            if templates:
                templates.sort(key=lambda t: t.success_rate, reverse=True)
                return templates[0]
        return None

    def increment_usage(self, template_id: str, approved: bool | None = None) -> None:
        with self._db() as session:
            t = session.get(Template, template_id)
            if t is None:
                return
            t.usage_count += 1
            if approved is True:
                t.success_count += 1

    def log_usage(
        self,
        template_id: str,
        message_id: str | None = None,
        category: str | None = None,
        confidence: float | None = None,
        operator_approved: bool | None = None,
        final_text: str | None = None,
        response_time_ms: int | None = None,
    ) -> None:
        with self._db() as session:
            log = TemplateUsageLog(
                template_id=template_id,
                message_id=str(message_id) if message_id else None,
                category=category,
                confidence=confidence,
                operator_approved=operator_approved,
                final_text=final_text,
                response_time_ms=response_time_ms,
            )
            session.add(log)
            session.flush()

    def _get_fallback(self) -> Template:
        import random
        text = random.choice(FALLBACK_TEXTS)
        t = Template(scope="fallback", text=text, category="general", name="fallback", slug="fallback")
        t.variables = []
        return t
