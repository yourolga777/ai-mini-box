from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Order


class OrderService:
    def __init__(self, repos: RepoContainer):
        self.repos = repos

    def create_from_message(
        self,
        message_id: int,
        contact_id: int,
        total_kopecks: int = 0,
        notes: str = "",
    ) -> Order:
        order = Order(
            contact_id=contact_id,
            total_kopecks=total_kopecks,
            notes=notes,
            status="new",
            source_message_id=message_id,
        )
        created = self.repos.orders.add(order)
        msg = self.repos.messages.get_by_id(message_id)
        if msg:
            msg.extracted_order_id = created.id
            self.repos.messages.update(msg)
        return created
