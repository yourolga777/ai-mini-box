from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai_mini_box.infrastructure.database import get_db
from ..models import Template
from ..templates.store import TemplateCreate, TemplateStore, TemplateUpdate

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


class TemplateResponse(BaseModel):
    id: str
    scope: str
    category: str
    name: str
    slug: str
    text: str
    variables: list[str] = []
    defaults: dict[str, str] = {}
    triggers: list[str] = []
    confidence_min: float = 0.6
    usage_count: int = 0
    success_count: int = 0
    version: int = 1
    is_active: int = 1
    is_archived: int = 0
    created_by_id: str | None = None
    updated_by_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    success_rate: float = 0.0

    model_config = {"from_attributes": True}


class TemplateCreateBody(BaseModel):
    scope: str
    category: str
    name: str
    text: str
    variables: list[str] = []
    defaults: dict[str, str] = {}
    triggers: list[str] = []
    confidence_min: float = 0.6


class TemplateUpdateBody(BaseModel):
    scope: Optional[str] = None
    category: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None
    variables: Optional[list[str]] = None
    defaults: Optional[dict[str, str]] = None
    triggers: Optional[list[str]] = None
    confidence_min: Optional[float] = None
    is_active: Optional[int] = None
    is_archived: Optional[int] = None


def _get_store() -> TemplateStore:
    return TemplateStore(get_db)


@router.get("/", response_model=list[TemplateResponse])
def list_templates(
    scope: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    search: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    store = _get_store()
    templates = store.list(
        scope=scope,
        category=category,
        is_active=is_active if is_active is not None else True,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [_to_response(t) for t in templates]


@router.post("/", response_model=TemplateResponse, status_code=201)
def create_template(body: TemplateCreateBody):
    store = _get_store()
    data = TemplateCreate(
        scope=body.scope,
        category=body.category,
        name=body.name,
        text=body.text,
        variables=body.variables,
        defaults=body.defaults,
        triggers=body.triggers,
        confidence_min=body.confidence_min,
    )
    t = store.create(data)
    return _to_response(t)


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str):
    store = _get_store()
    t = store.get(template_id)
    if t is None:
        raise HTTPException(404, "Template not found")
    return _to_response(t)


@router.patch("/{template_id}", response_model=TemplateResponse)
def update_template(template_id: str, body: TemplateUpdateBody):
    store = _get_store()
    data = TemplateUpdate(**body.model_dump(exclude_defaults=True))
    t = store.update(template_id, data)
    if t is None:
        raise HTTPException(404, "Template not found")
    return _to_response(t)


@router.delete("/{template_id}")
def delete_template(template_id: str, hard: bool = Query(False)):
    store = _get_store()
    t = store.get(template_id)
    if t is None:
        raise HTTPException(404, "Template not found")
    if t.scope == "system" and not hard:
        raise HTTPException(400, "Cannot delete system template")
    store.delete(template_id, hard=hard)
    return {"ok": True}


@router.get("/suggest")
def suggest_templates(
    message: str = Query(...),
    category: Optional[str] = Query(None),
    limit: int = Query(5),
):
    store = _get_store()
    result = store.find_best(
        category=category or "question",
        text=message,
        entities={},
        confidence=0.6,
    )
    if result:
        return [_to_response(result)]
    return []


@router.post("/{template_id}/use")
def log_template_use(
    template_id: str,
    message_id: Optional[int] = Query(None),
    operator_approved: Optional[bool] = Query(None),
    final_text: Optional[str] = Query(None),
    response_time_ms: int = 0,
):
    store = _get_store()
    store.increment_usage(template_id, approved=operator_approved)
    store.log_usage(
        template_id=template_id,
        message_id=str(message_id) if message_id else None,
        operator_approved=operator_approved,
        final_text=final_text,
        response_time_ms=response_time_ms,
    )
    return {"ok": True}


@router.post("/{template_id}/approve")
def approve_learned_template(template_id: str):
    store = _get_store()
    t = store.get(template_id)
    if t is None:
        raise HTTPException(404, "Template not found")
    if t.scope != "learned":
        raise HTTPException(400, "Only learned templates can be approved")
    store.update(template_id, TemplateUpdate(scope="business"))
    return {"ok": True}


@router.get("/stats")
def get_template_stats(period: str = Query("30d")):
    store = _get_store()
    templates = store.list(is_active=True)
    total_usage = sum(t.usage_count for t in templates)
    total_success = sum(t.success_count for t in templates)
    return {
        "total_templates": len(templates),
        "total_usage": total_usage,
        "total_success": total_success,
        "success_rate": round((total_success / total_usage * 100) if total_usage > 0 else 0, 1),
    }


def _to_response(t: Template) -> TemplateResponse:
    return TemplateResponse(
        id=t.id,
        scope=t.scope,
        category=t.category,
        name=t.name,
        slug=t.slug,
        text=t.text,
        variables=t.variables,
        defaults=t.defaults,
        triggers=t.triggers,
        confidence_min=t.confidence_min or 0.6,
        usage_count=t.usage_count or 0,
        success_count=t.success_count or 0,
        version=t.version or 1,
        is_active=t.is_active or 1,
        is_archived=t.is_archived or 0,
        created_by_id=t.created_by_id,
        updated_by_id=t.updated_by_id,
        created_at=str(t.created_at) if t.created_at else None,
        updated_at=str(t.updated_at) if t.updated_at else None,
        success_rate=t.success_rate,
    )
