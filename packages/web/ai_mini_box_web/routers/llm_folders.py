from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ai_mini_box.core.services.registry import get_service
from ai_mini_box.infrastructure.database import get_db, get_session

ALLOWED_COLORS = {
    "#2563eb", "#16a34a", "#dc2626", "#ca8a04", "#8b5cf6", "#ec4899",
    "#f97316", "#14b8a6", "#6366f1", "#84cc16", "#06b6d4", "#e11d48",
}

router = APIRouter()


@router.get("/llm/health")
def llm_health():
    llm_svc = get_service("llm")
    if llm_svc is None:
        return {
            "status": "not_initialized",
            "model": None,
            "services": {"auto_processor": "running" if get_service("auto_processor") else "stopped"},
        }
    try:
        provider = llm_svc.provider
        model_name = getattr(provider, "model_name", None) or getattr(getattr(provider, "config", None), "model_path", None)
        if model_name:
            return {"status": "ok", "model": model_name, "services": {"auto_processor": "running" if get_service("auto_processor") else "stopped"}}
        return {"status": "no_model", "model": None, "services": {"auto_processor": "running" if get_service("auto_processor") else "stopped"}}
    except Exception:
        return {"status": "no_model", "model": None, "services": {"auto_processor": "running" if get_service("auto_processor") else "stopped"}}


class _FolderCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    color: str = "#2563eb"


class _FolderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    color: Optional[str] = None


class _AssignRequest(BaseModel):
    message_id: int


class _CategoryAssignRequest(BaseModel):
    category_id: int


class _BatchAssignRequest(BaseModel):
    message_ids: list[int]
    category_id: int


message_categories_router = APIRouter()


def _get_db_session():
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _llm_models():
    try:
        from ai_mini_box_llm.models import MessageCategory, MessageCategoryAssignment
        return MessageCategory, MessageCategoryAssignment
    except ImportError:
        raise HTTPException(502, detail="LLM plugin not installed", headers={"X-Error-Code": "ERR_LLM_NOT_INSTALLED"})


def _validate_color(color: str):
    if color not in ALLOWED_COLORS:
        raise HTTPException(422, detail=f"Invalid color. Allowed: {', '.join(sorted(ALLOWED_COLORS))}")


@router.get("/folders")
def list_folders(session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    cats = session.execute(select(MC).order_by(MC.id)).scalars().all()
    result = []
    for c in cats:
        count = session.execute(
            select(func.count()).select_from(MCA.__table__).where(MCA.category_id == c.id)
        ).scalar() or 0
        result.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "color": c.color,
            "is_system": c.is_system,
            "message_count": count,
        })
    return result


@router.post("/folders", status_code=201)
def create_folder(body: _FolderCreate, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    _validate_color(body.color)
    existing = session.execute(select(MC).where(MC.name == body.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(409, detail=f"Folder '{body.name}' already exists")
    cat = MC(name=body.name, description=body.description, color=body.color, is_system=False)
    session.add(cat)
    session.flush()
    session.refresh(cat)
    return {"id": cat.id, "name": cat.name, "description": cat.description, "color": cat.color, "is_system": False, "message_count": 0}


@router.put("/folders/{folder_id}")
def update_folder(folder_id: int, body: _FolderUpdate, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    cat = session.get(MC, folder_id)
    if cat is None:
        raise HTTPException(404, detail="Folder not found")
    if body.name is not None:
        if cat.is_system:
            raise HTTPException(403, detail="Cannot rename system folder")
        cat.name = body.name
    if body.description is not None:
        cat.description = body.description
    if body.color is not None:
        _validate_color(body.color)
        cat.color = body.color
    session.flush()
    session.refresh(cat)
    return {"id": cat.id, "name": cat.name, "description": cat.description, "color": cat.color, "is_system": cat.is_system}


@router.delete("/folders/{folder_id}")
def delete_folder(folder_id: int, mode: str = Query("move", pattern="^(move|delete_messages)$"), session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    cat = session.get(MC, folder_id)
    if cat is None:
        raise HTTPException(404, detail="Folder not found")
    if cat.is_system:
        raise HTTPException(403, detail="Cannot delete system folder")

    assignment_ids = session.execute(
        select(MCA.message_id).where(MCA.category_id == folder_id)
    ).scalars().all()

    if mode == "delete_messages" and assignment_ids:
        from ai_mini_box.infrastructure.orm_models import MessageModel
        for mid in assignment_ids:
            orm_msg = session.get(MessageModel, mid)
            if orm_msg:
                session.delete(orm_msg)
        session.flush()

    session.execute(MCA.__table__.delete().where(MCA.category_id == folder_id))
    session.delete(cat)
    session.flush()
    return {"ok": True, "mode": mode, "messages_affected": len(assignment_ids)}


@router.get("/folders/{folder_id}/messages")
def list_folder_messages(folder_id: int, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    cat = session.get(MC, folder_id)
    if cat is None:
        raise HTTPException(404, detail="Folder not found")
    message_ids = session.execute(
        select(MCA.message_id).where(MCA.category_id == folder_id)
    ).scalars().all()
    return message_ids


@router.post("/folders/{folder_id}/assign")
def assign_message(folder_id: int, body: _AssignRequest, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    cat = session.get(MC, folder_id)
    if cat is None:
        raise HTTPException(404, detail="Folder not found")

    from ai_mini_box.core.container import RepoContainer
    repos = RepoContainer(session)
    msg = repos.messages.get_by_id(body.message_id)
    if msg is None:
        raise HTTPException(404, detail="Message not found")

    existing = session.execute(
        select(MCA).where(MCA.message_id == body.message_id, MCA.category_id == folder_id)
    ).scalar_one_or_none()
    if existing:
        return {"ok": True, "already_assigned": True}

    session.add(MCA(message_id=body.message_id, category_id=folder_id, assigned_by="manual"))
    session.flush()
    return {"ok": True, "already_assigned": False}


@router.post("/folders/{folder_id}/unassign")
def unassign_message(folder_id: int, body: _AssignRequest, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    cat = session.get(MC, folder_id)
    if cat is None:
        raise HTTPException(404, detail="Folder not found")

    existing = session.execute(
        select(MCA).where(MCA.message_id == body.message_id, MCA.category_id == folder_id)
    ).scalar_one_or_none()
    if existing is None:
        return {"ok": True, "was_assigned": False}

    session.delete(existing)
    session.flush()
    return {"ok": True, "was_assigned": True}


@router.post("/process")
def run_auto_processor():
    svc = get_service("auto_processor")
    if svc is None:
        raise HTTPException(502, detail="AutoProcessor service not available (LLM plugin not installed)", headers={"X-Error-Code": "ERR_LLM_NOT_RUNNING"})

    from ai_mini_box.core.container import RepoContainer
    from ai_mini_box.infrastructure.database import get_db as _get_db
    from ai_mini_box.core.models import Message

    with _get_db() as session:
        repos = RepoContainer(session)
        count = 0
        for msg in repos.messages.list(limit=50):
            if not msg.text:
                continue

            try:
                from ai_mini_box_llm.models import MessageCategoryAssignment
                existing = session.execute(
                    select(MessageCategoryAssignment).where(MessageCategoryAssignment.message_id == msg.id)
                ).scalar_one_or_none()
                if existing:
                    continue
            except ImportError:
                pass

            contact = None
            if msg.contact_id:
                try:
                    contact = repos.contacts.get_by_id(msg.contact_id)
                except Exception:
                    pass

            result = svc.process(msg, contact or Message())
            if result.contact_updated or result.task_created:
                count += 1

    return {"ok": True, "processed": count}


@message_categories_router.post("/api/messages/{message_id}/categories", status_code=201)
def assign_category_to_message(message_id: int, body: _CategoryAssignRequest, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()

    cat = session.get(MC, body.category_id)
    if cat is None:
        raise HTTPException(404, detail="Category not found")

    from ai_mini_box.core.container import RepoContainer
    repos = RepoContainer(session)
    msg = repos.messages.get_by_id(message_id)
    if msg is None:
        raise HTTPException(404, detail="Message not found")

    existing = session.execute(
        select(MCA).where(MCA.message_id == message_id, MCA.category_id == body.category_id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, detail="Already assigned")

    session.add(MCA(message_id=message_id, category_id=body.category_id, assigned_by="manual"))
    session.flush()
    return {"ok": True}


@message_categories_router.delete("/api/messages/{message_id}/categories/{category_id}")
def remove_category_from_message(message_id: int, category_id: int, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()

    existing = session.execute(
        select(MCA).where(MCA.message_id == message_id, MCA.category_id == category_id)
    ).scalar_one_or_none()
    if existing is None:
        raise HTTPException(404, detail="Assignment not found")
    if existing.assigned_by == "system":
        raise HTTPException(403, detail="Cannot remove system assignment")

    session.delete(existing)
    session.flush()
    return {"ok": True}


@router.post("/assign-all")
def assign_all(limit: int = Query(50, ge=1, le=500)):
    svc = get_service("auto_processor")
    if svc is None:
        raise HTTPException(502, detail="AutoProcessor service not available (LLM plugin not installed)", headers={"X-Error-Code": "ERR_LLM_NOT_RUNNING"})
    import sqlite3, time
    for attempt, delay in enumerate([1, 2, 4]):
        try:
            checked, assigned = svc.process_all(limit=limit)
            return {"checked": checked, "assigned": assigned}
        except sqlite3.OperationalError as e:
            if "database is locked" not in str(e) or attempt == 2:
                raise HTTPException(500, detail=f"AutoProcessor error: {e}")
            time.sleep(delay)
    raise HTTPException(500, detail="AutoProcessor error: database is locked after 3 retries")


@router.post("/folders/reorder")
def reorder_folders(body: dict, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    order = body.get("order", [])
    for i, fid in enumerate(order):
        cat = session.get(MC, fid)
        if cat:
            cat.order = i
    session.flush()
    return {"ok": True}


@router.post("/batch-assign")
def batch_assign(body: _BatchAssignRequest, session: Session = Depends(_get_db_session)):
    MC, MCA = _llm_models()
    cat = session.get(MC, body.category_id)
    if cat is None:
        raise HTTPException(404, detail="Category not found")

    from ai_mini_box.core.container import RepoContainer
    repos = RepoContainer(session)

    assigned = 0
    errors = []
    for mid in body.message_ids:
        msg = repos.messages.get_by_id(mid)
        if msg is None:
            errors.append({"message_id": mid, "error": "Message not found"})
            continue
        existing = session.execute(
            select(MCA).where(MCA.message_id == mid, MCA.category_id == body.category_id)
        ).scalar_one_or_none()
        if existing:
            assigned += 1
            continue
        session.add(MCA(message_id=mid, category_id=body.category_id, assigned_by="manual"))
        assigned += 1

    session.flush()
    return {"assigned": assigned, "errors": errors}
