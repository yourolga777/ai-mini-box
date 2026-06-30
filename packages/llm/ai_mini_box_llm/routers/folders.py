from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_mini_box.infrastructure.database import get_db

from ..models import MessageCategory, MessageCategoryAssignment

router = APIRouter()


class CategoryOut(BaseModel):
    id: int
    name: str
    description: str
    color: str
    is_system: bool

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
    description: str = ""
    color: str = "#6b7280"


@router.get("", response_model=list[CategoryOut])
def list_categories(session: Session = Depends(get_db)):
    cats = session.execute(select(MessageCategory).order_by(MessageCategory.id)).scalars().all()
    return [CategoryOut.model_validate(c) for c in cats]


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(body: CategoryCreate, session: Session = Depends(get_db)):
    existing = session.execute(
        select(MessageCategory).where(MessageCategory.name == body.name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(400, f"Category '{body.name}' already exists")

    cat = MessageCategory(
        name=body.name,
        description=body.description,
        color=body.color,
        is_system=False,
    )
    session.add(cat)
    session.flush()
    session.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.delete("/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_db)):
    cat = session.get(MessageCategory, category_id)
    if cat is None:
        raise HTTPException(404, "Category not found")
    if cat.is_system:
        raise HTTPException(400, "Cannot delete system category")

    session.execute(
        MessageCategoryAssignment.__table__.delete().where(
            MessageCategoryAssignment.category_id == category_id
        )
    )
    session.delete(cat)
    session.flush()
    return {"ok": True}


@router.get("/{category_id}/messages", response_model=list[int])
def list_category_messages(category_id: int, session: Session = Depends(get_db)):
    cat = session.get(MessageCategory, category_id)
    if cat is None:
        raise HTTPException(404, "Category not found")
    assignments = session.execute(
        select(MessageCategoryAssignment).where(
            MessageCategoryAssignment.category_id == category_id
        )
    ).scalars().all()
    return [a.message_id for a in assignments]


@router.post("/classify/{message_id}")
def classify_message(
    message_id: int,
    session: Session = Depends(get_db),
):
    from ai_mini_box.core.container import RepoContainer
    from ai_mini_box.core.services.registry import get_service as _get_service

    llm = _get_service("llm")
    if llm is None:
        raise HTTPException(503, "LLM service not available")

    repos = RepoContainer(session)
    msg = repos.messages.get_by_id(message_id)
    if msg is None:
        raise HTTPException(404, "Message not found")

    cats = session.execute(select(MessageCategory)).scalars().all()
    if not cats:
        raise HTTPException(400, "No categories defined")

    best = llm.classify_category(msg.text, cats)

    existing = session.execute(
        select(MessageCategoryAssignment).where(
            MessageCategoryAssignment.message_id == message_id,
            MessageCategoryAssignment.category_id == best.id,
        )
    ).scalar_one_or_none()
    if not existing:
        session.add(MessageCategoryAssignment(
            message_id=message_id,
            category_id=best.id,
            assigned_by="auto",
        ))

    session.flush()
    return {"category_id": best.id, "category_name": best.name}
