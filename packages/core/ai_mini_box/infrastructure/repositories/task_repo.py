from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_mini_box.core.exceptions import NotFoundError
from ai_mini_box.core.models import Task
from ai_mini_box.core.repositories import TaskRepo
from ai_mini_box.infrastructure.mapping import task_from_orm, task_to_orm
from ai_mini_box.infrastructure.orm_models import TaskModel


class SqliteTaskRepo(TaskRepo):
    def __init__(self, session: Session):
        self.session = session

    def query(self):
        from ai_mini_box.core.repositories import QueryBuilder

        all_items = self.list(limit=10000)
        return QueryBuilder(all_items)

    def list(self, limit=50, offset=0, **filters):
        stmt = select(TaskModel)
        for key, value in filters.items():
            if value is not None and hasattr(TaskModel, key):
                stmt = stmt.where(getattr(TaskModel, key) == value)
        stmt = stmt.order_by(TaskModel.due_date, TaskModel.due_time).limit(limit).offset(offset)
        orm_objs = self.session.execute(stmt).scalars().all()
        return [task_from_orm(o) for o in orm_objs]

    def get_by_id(self, id: int) -> Optional[Task]:
        orm_obj = self.session.get(TaskModel, id)
        return task_from_orm(orm_obj) if orm_obj else None

    def add(self, task: Task) -> Task:
        orm_obj = task_to_orm(task)
        self.session.add(orm_obj)
        self.session.flush()
        self.session.refresh(orm_obj)
        return task_from_orm(orm_obj)

    def update(self, task: Task) -> Task:
        orm_obj = self.session.get(TaskModel, task.id)
        if not orm_obj:
            raise NotFoundError("Task", task.id)
        for field, value in task.model_dump(exclude_unset=True).items():
            setattr(orm_obj, field, value)
        self.session.flush()
        self.session.refresh(orm_obj)
        return task_from_orm(orm_obj)

    def delete(self, id: int) -> bool:
        orm_obj = self.session.get(TaskModel, id)
        if not orm_obj:
            return False
        self.session.delete(orm_obj)
        self.session.flush()
        return True
