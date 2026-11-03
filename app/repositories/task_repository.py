# pyrefly: ignore[missing-import]
from sqlalchemy import ColumnElement, or_
# pyrefly: ignore[missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskPriority, TaskStatus


class TaskRepository(BaseRepository[Task]):
    """Asynchronous repository for Task model built on BaseRepository[Task]."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def list_tasks(
        self,
        *,
        page: int = 1,
        size: int = 10,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        project_id: int | None = None,
        assignee_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int, int]:
        filters: list[ColumnElement[bool]] = []
        if status is not None:
            filters.append(Task.status == status)
        if priority is not None:
            filters.append(Task.priority == priority)
        if project_id is not None:
            filters.append(Task.project_id == project_id)
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
        return await self.get_multi_paginated(page=page, size=size, filters=filters)
