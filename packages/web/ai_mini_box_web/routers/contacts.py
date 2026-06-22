from fastapi import APIRouter, Depends, HTTPException, Query

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Contact
from ai_mini_box_web.dependencies import get_repos

router = APIRouter()


@router.get("/")
def list_contacts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
):
    if search:
        items = repos.contacts.search(search)
        return [c.model_dump() for c in items]
    items = repos.contacts.list(limit=limit, offset=offset)
    return [c.model_dump() for c in items]


@router.get("/{item_id}")
def get_contact(item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.contacts.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return item.model_dump()


@router.post("/", status_code=201)
def create_contact(data: dict, repos: RepoContainer = Depends(get_repos)):
    contact = Contact(**data)
    created = repos.contacts.add(contact)
    return created.model_dump()


@router.put("/{item_id}")
def update_contact(item_id: int, data: dict, repos: RepoContainer = Depends(get_repos)):
    existing = repos.contacts.get_by_id(item_id)
    if existing is None:
        raise HTTPException(404)
    updated = existing.model_copy(update=data)
    result = repos.contacts.update(updated)
    return result.model_dump()


@router.delete("/{item_id}", status_code=204)
def delete_contact(item_id: int, repos: RepoContainer = Depends(get_repos)):
    if not repos.contacts.delete(item_id):
        raise HTTPException(404)
