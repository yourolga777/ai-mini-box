from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Topic(str, Enum):
    PRICES = "Цены"
    ORDER = "Заказ"
    COMPLAINT = "Жалоба"
    SCHEDULE = "График"
    OTHER = "Другое"


class MessageSource(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    MANUAL = "manual"


class OrderStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Contact(BaseModel):
    id: Optional[int] = None
    name: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None
    whatsapp: Optional[str] = None
    source: MessageSource = MessageSource.MANUAL
    notes: Optional[str] = None
    total_spent: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Product(BaseModel):
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    price_kopecks: int = 0
    stock: int = 0
    unit: str = "шт"
    category: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    id: Optional[int] = None
    source: MessageSource = MessageSource.MANUAL
    external_id: Optional[str] = None
    chat_id: Optional[str] = None
    contact_id: Optional[int] = None
    text: str = ""
    topic: Optional[Topic] = None
    draft_response: Optional[str] = None
    sent_response: bool = False
    received_at: datetime = Field(default_factory=datetime.now)


class Order(BaseModel):
    id: Optional[int] = None
    contact_id: Optional[int] = None
    status: OrderStatus = OrderStatus.NEW
    total_kopecks: int = 0
    notes: Optional[str] = None
    source_message_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
