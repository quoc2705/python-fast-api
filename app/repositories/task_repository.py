from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import TaskPriority, TaskStatus
from app.models.label import TaskLabel
from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Asynchronous repository for Task and TaskLabel models."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def get_by_id_with_details(self, task_id: int) -> Task | None:
        stmt = (
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.labels),
                selectinload(Task.comments),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        project_id: int | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int, int]:
        filters: list[ColumnElement[bool]] = []
        if project_id is not None:
            filters.append(Task.project_id == project_id)
        if status is not None:
            filters.append(Task.status == status)
        if priority is not None:
            filters.append(Task.priority == priority)
        if assignee_id is not None:
            filters.append(Task.assignee_id == assignee_id)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                )
            )
        return await self.get_multi_paginated(page=page, limit=limit, filters=filters)

    async def attach_label(self, task_id: int, label_id: int) -> None:
        stmt = select(TaskLabel).where(
            TaskLabel.task_id == task_id,
            TaskLabel.label_id == label_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            self.session.add(TaskLabel(task_id=task_id, label_id=label_id))
            await self.session.commit()

    async def detach_label(self, task_id: int, label_id: int) -> bool:
        stmt = select(TaskLabel).where(
            TaskLabel.task_id == task_id,
            TaskLabel.label_id == label_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            return False
        await self.session.delete(existing)
        await self.session.commit()
        return True
