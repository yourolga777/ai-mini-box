from fastapi import APIRouter, Depends, HTTPException, Query

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Product
from ai_mini_box_web.dependencies import get_repos

router = APIRouter()


@router.get("/")
def list_products(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
):
    if search:
        items = repos.products.search(search)
        return [p.model_dump() for p in items]
    items = repos.products.list(limit=limit, offset=offset)
    return [p.model_dump() for p in items]


@router.get("/{item_id}")
def get_product(item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.products.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return item.model_dump()


@router.post("/", status_code=201)
def create_product(data: dict, repos: RepoContainer = Depends(get_repos)):
    product = Product(**data)
    created = repos.products.add(product)
    return created.model_dump()


@router.put("/{item_id}")
def update_product(item_id: int, data: dict, repos: RepoContainer = Depends(get_repos)):
    existing = repos.products.get_by_id(item_id)
    if existing is None:
        raise HTTPException(404)
    updated = existing.model_copy(update=data)
    result = repos.products.update(updated)
    return result.model_dump()


@router.delete("/{item_id}", status_code=204)
def delete_product(item_id: int, repos: RepoContainer = Depends(get_repos)):
    if not repos.products.delete(item_id):
        raise HTTPException(404)
