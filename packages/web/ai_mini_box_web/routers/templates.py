from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

from ai_mini_box.infrastructure.database import get_db
from ai_mini_box_web.dependencies import get_repos

router = APIRouter()


class TemplateCreate(BaseModel):
    scope: str = "business"
    category: str
    name: str
    text: str
    variables: list[str] = []
    defaults: dict[str, str] = {}
    triggers: list[str] = []
    confidence_min: float = 0.6
    is_active: bool = True

    @field_validator("scope")
    @classmethod
    def only_business(cls, v: str) -> str:
        if v != "business":
            raise ValueError("Only 'business' scope allowed on create")
        return v


class TemplateUpdate(BaseModel):
    name: str | None = None
    text: str | None = None
    variables: list[str] | None = None
    defaults: dict[str, str] | None = None
    triggers: list[str] | None = None
    confidence_min: float | None = None
    is_active: bool | None = None


class TemplateResponse(BaseModel):
    id: str
    scope: str
    category: str
    name: str
    slug: str
    text: str
    variables: list[str]
    defaults: dict[str, str]
    triggers: list[str]
    confidence_min: float
    usage_count: int
    success_count: int
    success_rate: float
    version: int
    is_active: bool
    is_archived: bool
    created_at: str | None
    updated_at: str | None

    model_config = {"from_attributes": True}


class UseTemplateBody(BaseModel):
    message_id: str | None = None
    operator_approved: bool | None = None
    operator_edited: bool = False
    final_text: str | None = None
    response_time_ms: int = 0


def _get_store():
    try:
        from ai_mini_box_llm.templates.store import TemplateStore
        return TemplateStore(get_db)
    except ImportError:
        return None


def _to_response(t) -> TemplateResponse:
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
        success_rate=t.success_rate,
        version=t.version or 1,
        is_active=bool(t.is_active),
        is_archived=bool(t.is_archived),
        created_at=str(t.created_at) if t.created_at else None,
        updated_at=str(t.updated_at) if t.updated_at else None,
    )


@router.get("/", response_model=list[TemplateResponse])
def list_templates(
    scope: str | None = Query(None),
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    store = _get_store()
    if store is None:
        raise HTTPException(502, detail="LLM plugin not installed")
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
def create_template(body: TemplateCreate):
    store = _get_store()
    if store is None:
        raise HTTPException(502, detail="LLM plugin not installed")
    try:
        from ai_mini_box_llm.templates.store import TemplateCreate as TC
    except ImportError:
        raise HTTPException(502, detail="LLM plugin not installed")
    data = TC(
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


@router.get("/suggest")
def suggest_templates(
    message: str = Query(...),
    category: str | None = Query(None),
    limit: int = Query(5, ge=1, le=20),
):
    store = _get_store()
    if store is None:
        raise HTTPException(502, detail="LLM plugin not installed")
    from ai_mini_box_llm.pipeline import ProcessingContext
    from ai_mini_box.core.services.registry import get_service
    pipeline = get_service("llm")
    if pipeline:
        context = ProcessingContext(text=message, category=category)
        result = pipeline.process(message, context)
        templates = store.list(
            category=result.category,
            is_active=True,
            limit=limit,
        )
        return {
            "templates": [_to_response(t) for t in templates],
            "entities": result.entities,
            "category": result.category,
            "confidence": result.confidence,
        }
    result = store.find_best(category=category or "question", text=message, entities={}, confidence=0.6)
    if result:
        return {
            "templates": [_to_response(result)],
            "entities": {},
            "category": result.category,
            "confidence": 0.6,
        }
    return {"templates": [], "entities": {}, "category": None, "confidence": 0.0}


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str):
    store = _get_store()
    if store is None:
        raise HTTPException(502, detail="LLM plugin not installed")
    t = store.get(template_id)
    if t is None:
        raise HTTPException(404, detail="Template not found")
    return _to_response(t)


@router.patch("/{template_id}", response_model=TemplateResponse)
def update_template(template_id: str, body: TemplateUpdate):
    store = _get_store()
    if store is None:
        raise HTTPException(502, detail="LLM plugin not installed")
    t = store.get(template_id)
    if t is None:
        raise HTTPException(404, detail="Template not found")
    if t.scope == "system":
        raise HTTPException(400, detail="Cannot edit system template")
    try:
        from ai_mini_box_llm.templates.store import TemplateUpdate as TU
    except ImportError:
        raise HTTPException(502, detail="LLM plugin not installed")
    data = TU(**body.model_dump(exclude_defaults=True))
    updated = store.update(template_id, data)
    if updated is None:
        raise HTTPException(404, detail="Template not found")
    return _to_response(updated)


@router.delete("/{template_id}")
def delete_template(template_id: str, hard: bool = Query(False)):
    store = _get_store()
    if store is None:
        raise HTTPException(502, detail="LLM plugin not installed")
    t = store.get(template_id)
    if t is None:
        raise HTTPException(404, detail="Template not found")
    if t.scope == "system" and not hard:
        raise HTTPException(400, detail="Cannot delete system template")
    store.delete(template_id, hard=hard)
    return {"ok": True}


@router.post("/{template_id}/use")
def log_template_use(template_id: str, body: UseTemplateBody):
    store = _get_store()
    if store is None:
        raise HTTPException(502, detail="LLM plugin not installed")
    store.increment_usage(template_id, approved=body.operator_approved)
    store.log_usage(
        template_id=template_id,
        message_id=body.message_id,
        operator_approved=body.operator_approved,
        final_text=body.final_text,
        response_time_ms=body.response_time_ms,
    )
    return {"ok": True}


@router.post("/{template_id}/approve", response_model=TemplateResponse)
def approve_learned_template(template_id: str):
    store = _get_store()
    if store is None:
        raise HTTPException(502, detail="LLM plugin not installed")
    t = store.get(template_id)
    if t is None:
        raise HTTPException(404, detail="Template not found")
    if t.scope != "learned":
        raise HTTPException(400, detail="Only learned templates can be approved")
    try:
        from ai_mini_box_llm.templates.store import TemplateUpdate as TU
    except ImportError:
        raise HTTPException(502, detail="LLM plugin not installed")
    store.update(template_id, TU(scope="business"))
    updated = store.get(template_id)
    return _to_response(updated)
