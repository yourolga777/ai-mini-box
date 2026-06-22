from ai_mini_box.core.models import Contact, Message, Order, Product
from ai_mini_box.infrastructure.orm_models import (
    ContactModel,
    MessageModel,
    OrderModel,
    ProductModel,
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


def order_from_orm(orm_obj: OrderModel) -> Order:
    return Order.model_validate(orm_obj, from_attributes=True)
