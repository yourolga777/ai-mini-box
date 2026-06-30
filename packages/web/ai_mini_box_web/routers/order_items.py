from fastapi import APIRouter, Depends, HTTPException

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import OrderItem
from ai_mini_box_web.dependencies import get_repos

router = APIRouter()


@router.get("/{order_id}/items")
def list_order_items(order_id: int, repos: RepoContainer = Depends(get_repos)):
    return [i.model_dump() for i in repos.order_items.list_by_order(order_id)]


@router.get("/{order_id}/items/{item_id}")
def get_order_item(order_id: int, item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.order_items.get_by_id(item_id)
    if item is None or item.order_id != order_id:
        raise HTTPException(404)
    return item.model_dump()


@router.post("/{order_id}/items", status_code=201)
def create_order_item(order_id: int, data: dict, repos: RepoContainer = Depends(get_repos)):
    existing = repos.orders.get_by_id(order_id)
    if existing is None:
        raise HTTPException(404, detail="Order not found")
    product_id = data.get("product_id")
    if product_id is not None:
        product = repos.products.get_by_id(product_id)
        if product:
            data.setdefault("product_name", product.name)
            data.setdefault("price_kopecks", product.price_kopecks)
    item = OrderItem(order_id=order_id, **data)
    created = repos.order_items.add(item)
    return created.model_dump()


@router.put("/{order_id}/items/{item_id}")
def update_order_item(order_id: int, item_id: int, data: dict, repos: RepoContainer = Depends(get_repos)):
    existing = repos.order_items.get_by_id(item_id)
    if existing is None or existing.order_id != order_id:
        raise HTTPException(404)
    updated = existing.model_copy(update=data)
    result = repos.order_items.update(updated)
    return result.model_dump()


@router.delete("/{order_id}/items/{item_id}", status_code=204)
def delete_order_item(order_id: int, item_id: int, repos: RepoContainer = Depends(get_repos)):
    existing = repos.order_items.get_by_id(item_id)
    if existing is None or existing.order_id != order_id:
        raise HTTPException(404)
    repos.order_items.delete(item_id)
