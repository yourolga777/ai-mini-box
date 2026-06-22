from fastapi import APIRouter, Depends, HTTPException, Query

from ai_mini_box.core.container import RepoContainer
from ai_mini_box.core.models import Message, Topic
from ai_mini_box_web.dependencies import get_repos

router = APIRouter()


@router.get("/")
def list_messages(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    topic: Topic | None = Query(None),
    search: str | None = Query(None),
    repos: RepoContainer = Depends(get_repos),
):
    if search:
        items = repos.messages.search(search, topic=topic.value if topic else None)
        return [m.model_dump() for m in items]
    filters = {}
    if topic:
        filters["topic"] = topic
    items = repos.messages.list(limit=limit, offset=offset, **filters)
    return [m.model_dump() for m in items]


@router.get("/{item_id}")
def get_message(item_id: int, repos: RepoContainer = Depends(get_repos)):
    item = repos.messages.get_by_id(item_id)
    if item is None:
        raise HTTPException(404)
    return item.model_dump()


@router.post("/", status_code=201)
def create_message(data: dict, repos: RepoContainer = Depends(get_repos)):
    message = Message(**data)
    created = repos.messages.add(message)
    return created.model_dump()
