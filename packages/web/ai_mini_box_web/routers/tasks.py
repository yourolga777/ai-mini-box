from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Task
from ai_mini_box_web.dependencies import get_repos

router = APIRouter()


@router.get("")
def list_tasks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    due_date: str | None = Query(None),
    month: str | None = Query(None),
    status: str | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
):
    filters = {}
    if due_date:
        filters["due_date"] = due_date
    if status:
        filters["status"] = status
    items = repos.tasks.list(limit=limit, offset=offset, **filters)
    if month:
        items = [t for t in items if t.due_date.strftime("%Y-%m") == month]
    return [t.model_dump() for t in items]


@router.get("/{item_id}")
def get_task(item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.tasks.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return item.model_dump()


@router.post("", status_code=201)
def create_task(data: dict, repos: RepoContainer = Depends(get_repos)):
    task = Task(**data)
    created = repos.tasks.add(task)
    return created.model_dump()


@router.put("/{item_id}")
def update_task(item_id: int, data: dict, repos: RepoContainer = Depends(get_repos)):
    existing = repos.tasks.get_by_id(item_id)
    if existing is None:
        raise HTTPException(404)
    updated = existing.model_copy(update=data)
    result = repos.tasks.update(updated)
    return result.model_dump()


@router.delete("/{item_id}", status_code=204)
def delete_task(item_id: int, repos: RepoContainer = Depends(get_repos)):
    if not repos.tasks.delete(item_id):
        raise HTTPException(404)
