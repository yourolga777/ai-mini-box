from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from ..core.models import MessageSource, OrderStatus, Topic


class ContactModel(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[MessageSource] = mapped_column(
        Enum(MessageSource), default=MessageSource.MANUAL
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_spent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_kopecks: Mapped[int] = mapped_column(Integer, default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    unit: Mapped[str] = mapped_column(String(20), default="шт")
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[MessageSource] = mapped_column(
        Enum(MessageSource), default=MessageSource.MANUAL
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text, default="")
    topic: Mapped[Topic | None] = mapped_column(Enum(Topic), nullable=True)
    draft_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_response: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.NEW
    )
    total_kopecks: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
