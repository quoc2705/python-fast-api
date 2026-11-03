from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.label import Label
from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    """Asynchronous repository for Label model."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Label, session)

    async def list_by_project(
        self,
        project_id: int,
        *,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Label], int, int]:
        filters: list[ColumnElement[bool]] = [Label.project_id == project_id]
        return await self.get_multi_paginated(page=page, limit=limit, filters=filters)

