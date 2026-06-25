from fastapi import APIRouter, Depends, HTTPException, Query

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import KnowledgeBaseItem, Topic
from ai_mini_box_web.dependencies import get_repos

router = APIRouter()


@router.get("")
def list_kb(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    topic: Topic | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
):
    filters = {}
    if topic:
        filters["topic"] = topic
    items = repos.kb.list(limit=limit, offset=offset, **filters)
    return [m.model_dump() for m in items]


@router.get("/{item_id}")
def get_kb_item(item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.kb.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return item.model_dump()


@router.post("", status_code=201)
def create_kb_item(data: dict, repos: RepoContainer = Depends(get_repos)):
    item = KnowledgeBaseItem(**data)
    created = repos.kb.add(item)
    return created.model_dump()


@router.put("/{item_id}")
def update_kb_item(item_id: int, data: dict, repos: RepoContainer = Depends(get_repos)):
    existing = repos.kb.get_by_id(item_id)
    if existing is None:
        raise HTTPException(404)
    for key, value in data.items():
        setattr(existing, key, value)
    updated = repos.kb.update(existing)
    return updated.model_dump()


@router.delete("/{item_id}", status_code=204)
def delete_kb_item(item_id: int, repos: RepoContainer = Depends(get_repos)):
    ok = repos.kb.delete(item_id)
    if not ok:
        raise HTTPException(404)
