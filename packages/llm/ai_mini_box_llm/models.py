from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_mini_box.infrastructure.database import Base


class MessageCategory(Base):
    __tablename__ = "llm_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    color: Mapped[str] = mapped_column(String(7), default="#6b7280")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    assignments: Mapped[list["MessageCategoryAssignment"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class MessageCategoryAssignment(Base):
    __tablename__ = "llm_category_assignments"

    __table_args__ = (
        UniqueConstraint("message_id", "category_id", name="uq_msg_cat"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("llm_categories.id"), nullable=False)
    assigned_by: Mapped[str] = mapped_column(String(20), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    category: Mapped["MessageCategory"] = relationship(back_populates="assignments")


class TrainingLog(Base):
    __tablename__ = "training_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    category_predicted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category_corrected: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_order_predicted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_order_corrected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    template_id_used: Mapped[str | None] = mapped_column(String(32), nullable=True)
    operator_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    operator_edited: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    final_reply_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.now()


class Template(Base):
    __tablename__ = "templates"

    __table_args__ = (
        UniqueConstraint("scope", "slug", name="uq_templates_scope_slug"),
    )

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    scope = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    _variables = Column("variables", Text, default="[]")
    _defaults = Column("defaults", Text, default="{}")
    _triggers = Column("triggers", Text, default="[]")
    confidence_min = Column(Float, default=0.6)
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    version = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    is_archived = Column(Integer, default=0)
    created_by_id = Column(String(32), nullable=True)
    updated_by_id = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = uuid.uuid4().hex
        if self.usage_count is None:
            self.usage_count = 0
        if self.success_count is None:
            self.success_count = 0
        if self.is_active is None:
            self.is_active = 1
        if self.is_archived is None:
            self.is_archived = 0

    @property
    def variables(self) -> list[str]:
        try:
            return json.loads(self._variables)
        except (json.JSONDecodeError, TypeError):
            return []

    @variables.setter
    def variables(self, value: list[str]) -> None:
        self._variables = json.dumps(value, ensure_ascii=False)

    @property
    def defaults(self) -> dict:
        try:
            return json.loads(self._defaults)
        except (json.JSONDecodeError, TypeError):
            return {}

    @defaults.setter
    def defaults(self, value: dict) -> None:
        self._defaults = json.dumps(value, ensure_ascii=False)

    @property
    def triggers(self) -> list[str]:
        try:
            return json.loads(self._triggers)
        except (json.JSONDecodeError, TypeError):
            return []

    @triggers.setter
    def triggers(self, value: list[str]) -> None:
        self._triggers = json.dumps(value, ensure_ascii=False)

    @property
    def success_rate(self) -> float:
        count = self.usage_count or 0
        success = self.success_count or 0
        if count == 0:
            return 0.0
        return round((success / count) * 100, 1)


class TemplateUsageLog(Base):
    __tablename__ = "template_usage_log"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    template_id = Column(String(32), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String(32), nullable=True)
    category = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    was_used = Column(Integer, default=1)
    operator_approved = Column(Integer, nullable=True)
    operator_edited = Column(Integer, default=0)
    final_text = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = uuid.uuid4().hex
        if self.was_used is None:
            self.was_used = 1
        if self.operator_edited is None:
            self.operator_edited = 0


def classify_category_keyword(text: str, categories: list[MessageCategory]) -> MessageCategory | None:
    text_lower = text.lower()
    for cat in categories:
        if cat.name.lower() in text_lower:
            return cat
    for cat in categories:
        if cat.name == "Другое":
            return cat
    return categories[0] if categories else None
