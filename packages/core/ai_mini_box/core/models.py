from datetime import date, datetime
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
    extracted_phone: Optional[str] = None
    extracted_name: Optional[str] = None
    extracted_order_id: Optional[int] = None
    received_at: datetime = Field(default_factory=datetime.now)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    need_human: bool = False
    auto_replied: bool = False
    auto_reply_text: Optional[str] = None
    operator_context: Optional[str] = None


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(BaseModel):
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    due_date: date = Field(default_factory=date.today)
    due_time: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: str = "pending"
    contact_id: Optional[int] = None
    assignee: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Order(BaseModel):
    id: Optional[int] = None
    contact_id: Optional[int] = None
    status: OrderStatus = OrderStatus.NEW
    total_kopecks: int = 0
    notes: Optional[str] = None
    source_message_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class OrderItem(BaseModel):
    id: Optional[int] = None
    order_id: int
    product_id: Optional[int] = None
    product_name: str
    quantity: int = 1
    price_kopecks: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class BusinessConfig(BaseModel):
    company_name: str = "Название компании"
    work_hours: str = "Пн-Пт 9:00-18:00"
    delivery_info: str = "Условия доставки"
    return_policy: str = "Условия возврата"
    payment_methods: str = "Способы оплаты"
    contacts: str = "Контакты"
    faq: list[dict] = Field(default_factory=list)


class KnowledgeBaseItem(BaseModel):
    id: Optional[int] = None
    topic: Optional[Topic] = None
    question_keywords: list[str] = Field(default_factory=list)
    answer_text: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
