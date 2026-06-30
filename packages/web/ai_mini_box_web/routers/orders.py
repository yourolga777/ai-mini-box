from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Order, OrderStatus
from ai_mini_box.infrastructure.orm_models import ContactModel, OrderItemModel
from ai_mini_box_web.dependencies import get_repos, _get_db_session

router = APIRouter()


_VALID_TRANSITIONS = {
    OrderStatus.NEW: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: {OrderStatus.CANCELLED},
    OrderStatus.CANCELLED: set(),
}


def _enrich_order(order: Order, session) -> dict:
    d = order.model_dump()
    d["updated_at"] = d.get("updated_at", d["created_at"])
    items = session.execute(
        select(OrderItemModel).where(OrderItemModel.order_id == order.id)
    ).scalars().all()
    d["items"] = [
        {
            "id": i.id,
            "order_id": i.order_id,
            "product_id": i.product_id,
            "product_name": i.product_name,
            "quantity": i.quantity,
            "price_kopecks": i.price_kopecks,
            "created_at": str(i.created_at),
        }
        for i in items
    ]
    if order.contact_id:
        contact = session.get(ContactModel, order.contact_id)
        d["contact_name"] = contact.name if contact else "Удалённый контакт"
    else:
        d["contact_name"] = None
    return d


def _enrich_order_list(orders: list[Order], session) -> list[dict]:
    result = []
    for o in orders:
        d = o.model_dump()
        if o.contact_id:
            contact = session.get(ContactModel, o.contact_id)
            d["contact_name"] = contact.name if contact else "Удалённый контакт"
        else:
            d["contact_name"] = None
        result.append(d)
    return result


@router.get("")
def list_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: OrderStatus | None = Query(None),
    contact_id: int | None = Query(None),
    search: str | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
    session=Depends(_get_db_session),
):
    filters = {}
    if status:
        filters["status"] = status
    if contact_id is not None:
        filters["contact_id"] = contact_id
    items = repos.orders.list(limit=limit, offset=offset, sort="created_at", **filters)
    if search:
        search_lower = search.lower()
        items = [o for o in items if o.notes and search_lower in o.notes.lower()]
    if contact_id is None:
        return _enrich_order_list(items, session)
    return [o.model_dump() for o in items]


@router.get("/{item_id}")
def get_order(item_id: int, repos: RepoContainer = Depends(get_repos), session=Depends(_get_db_session)):
    item = repos.orders.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return _enrich_order(item, session)


@router.post("", status_code=201)
def create_order(data: dict, repos: RepoContainer = Depends(get_repos)):
    order = Order(**data)
    created = repos.orders.add(order)
    return created.model_dump()


@router.put("/{item_id}")
def update_order(item_id: int, data: dict, repos: RepoContainer = Depends(get_repos)):
    existing = repos.orders.get_by_id(item_id)
    if existing is None:
        raise HTTPException(404)
    if "status" in data:
        new_status = OrderStatus(data["status"])
        if new_status not in _VALID_TRANSITIONS.get(existing.status, set()):
            raise HTTPException(
                400,
                detail=f"Недопустимый переход статуса: {existing.status.value} → {new_status.value}",
            )
    updated = existing.model_copy(update=data)
    result = repos.orders.update(updated)
    return result.model_dump()


@router.delete("/{item_id}", status_code=204)
def delete_order(item_id: int, repos: RepoContainer = Depends(get_repos)):
    existing = repos.orders.get_by_id(item_id)
    if existing is None:
        raise HTTPException(404)
    repos.orders.delete(item_id)


@router.post("/from-message", status_code=201)
def create_order_from_message(data: dict, repos: RepoContainer = Depends(get_repos)):
    from ai_mini_box.core.services.order_service import OrderService

    svc = OrderService(repos)
    order = svc.create_from_message(
        message_id=data["message_id"],
        contact_id=data["contact_id"],
        total_kopecks=data.get("total_kopecks", 0),
        notes=data.get("notes", ""),
    )
    return order.model_dump()
