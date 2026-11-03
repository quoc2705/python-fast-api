from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ProjectStatus
from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Asynchronous repository for Project model."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Project, session)

    async def get_by_id_with_details(self, project_id: int) -> Project | None:
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.tasks),
                selectinload(Project.labels),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        workspace_id: int | None = None,
        status: ProjectStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Project], int, int]:
        filters: list[ColumnElement[bool]] = []
        if workspace_id is not None:
            filters.append(Project.workspace_id == workspace_id)
        if status is not None:
            filters.append(Project.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Project.name.ilike(pattern),
                    Project.description.ilike(pattern),
                )
            )
        return await self.get_multi_paginated(page=page, limit=limit, filters=filters)
