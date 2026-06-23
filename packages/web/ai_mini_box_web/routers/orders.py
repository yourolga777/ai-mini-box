from fastapi import APIRouter, Depends, HTTPException, Query

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Order, OrderStatus
from ai_mini_box_web.dependencies import get_repos

router = APIRouter()


@router.get("")
def list_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: OrderStatus | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
):
    filters = {}
    if status:
        filters["status"] = status
    items = repos.orders.list(limit=limit, offset=offset, **filters)
    return [o.model_dump() for o in items]


@router.get("/{item_id}")
def get_order(item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.orders.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return item.model_dump()


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
    updated = existing.model_copy(update=data)
    result = repos.orders.update(updated)
    return result.model_dump()
