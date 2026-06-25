import json

from ai_mini_box.core.models import Contact, KnowledgeBaseItem, Message, Order, Product, Task
from ai_mini_box.infrastructure.orm_models import (
    ContactModel,
    KnowledgeBaseModel,
    MessageModel,
    OrderModel,
    ProductModel,
    TaskModel,
)


def contact_to_orm(contact: Contact) -> ContactModel:
    return ContactModel(**contact.model_dump(exclude_unset=True))


def contact_from_orm(orm_obj: ContactModel) -> Contact:
    return Contact.model_validate(orm_obj, from_attributes=True)


def product_to_orm(product: Product) -> ProductModel:
    return ProductModel(**product.model_dump(exclude_unset=True))


def product_from_orm(orm_obj: ProductModel) -> Product:
    return Product.model_validate(orm_obj, from_attributes=True)


def message_to_orm(message: Message) -> MessageModel:
    return MessageModel(**message.model_dump(exclude_unset=True))


def message_from_orm(orm_obj: MessageModel) -> Message:
    return Message.model_validate(orm_obj, from_attributes=True)


def order_to_orm(order: Order) -> OrderModel:
    return OrderModel(**order.model_dump(exclude_unset=True))


def task_to_orm(task: Task) -> TaskModel:
    return TaskModel(**task.model_dump(exclude_unset=True))


def task_from_orm(orm_obj: TaskModel) -> Task:
    return Task.model_validate(orm_obj, from_attributes=True)


def order_from_orm(orm_obj: OrderModel) -> Order:
    return Order.model_validate(orm_obj, from_attributes=True)


def kb_item_to_orm(item: KnowledgeBaseItem) -> KnowledgeBaseModel:
    data = item.model_dump(exclude_unset=True)
    data["question_keywords"] = json.dumps(data.get("question_keywords", []), ensure_ascii=False)
    return KnowledgeBaseModel(**data)


def kb_item_from_orm(orm_obj: KnowledgeBaseModel) -> KnowledgeBaseItem:
    data = {c.name: getattr(orm_obj, c.name) for c in orm_obj.__table__.columns}
    data["question_keywords"] = json.loads(data.get("question_keywords", "[]"))
    return KnowledgeBaseItem.model_validate(data, from_attributes=True)
